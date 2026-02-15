"""
Supervisor Agent - Orchestrates multi-agent workflow using LangGraph.
"""

from typing import Annotated, TypedDict
import operator
from datetime import datetime, timezone

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .llm import get_llm
from services.trend_sources import TwitterTrendSource
from services.crypto_sources import CoinGeckoSource
from services.matching import MatchingService, RecommendationEngine
from services.notifications import WhatsAppNotificationService
from config.settings import config
from utils.logger import get_logger

logger = get_logger(__name__)


class SupervisorState(TypedDict):
    """State for the supervisor orchestration."""
    messages: Annotated[list[BaseMessage], operator.add]
    current_step: str
    trends: list[dict]
    cryptos: list[dict]
    recommendations: list[dict]
    notifications_sent: int
    errors: list[str]


class CryptoScoutSupervisor:
    """
    Multi-agent supervisor that orchestrates the crypto scout workflow.
    Uses direct service calls + LLM for analysis/reasoning.
    """

    def __init__(self):
        self.checkpointer = MemorySaver()

        # Initialize services
        self.twitter_source = TwitterTrendSource()
        self.crypto_source = CoinGeckoSource()
        self.matching_service = MatchingService()
        self.recommendation_engine = RecommendationEngine()

        # Initialize LLM
        self.llm = get_llm()

        # Initialize notifications (WhatsApp only)
        self.notifier = WhatsAppNotificationService()
        if not self.notifier.is_configured():
            logger.warning("WhatsApp notifications not configured, will log only")

        # Build the graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the supervisor orchestration graph."""

        async def init_node(state: SupervisorState) -> dict:
            """Initialize the workflow."""
            logger.info("Supervisor: Initializing crypto scout workflow...")
            return {
                "messages": [AIMessage(content="🚀 Crypto Scout activated. Starting scan...")],
                "current_step": "trend_discovery",
            }

        async def trend_discovery_node(state: SupervisorState) -> dict:
            """Discover trends from Twitter using both approaches."""
            logger.info("Supervisor: Discovering trends from Twitter...")

            trends = []
            crypto_mentions = []
            errors = state.get("errors", [])

            # APPROACH 1: General viral trends (penguin, pepe, etc.)
            try:
                logger.info("Fetching general viral trends...")
                twitter_trends = await self.twitter_source.fetch_trends(limit=10)
                trends.extend(twitter_trends)
            except Exception as e:
                logger.error(f"Twitter trends fetch failed: {e}")
                errors.append(f"Twitter trends: {str(e)}")

            # APPROACH 2: Crypto-specific mentions ($PENGU, $PEPE, etc.)
            try:
                logger.info("Fetching crypto-specific mentions...")
                crypto_mentions = await self.twitter_source.fetch_crypto_mentions(limit=10)
            except Exception as e:
                logger.error(f"Crypto mentions fetch failed: {e}")
                errors.append(f"Crypto mentions: {str(e)}")

            # Convert general trends to dict
            trends_data = [
                {
                    "keyword": t.keyword,
                    "virality": t.virality_score,
                    "source": t.source.value,
                    "volume": t.volume,
                    "type": "general_trend",
                }
                for t in trends
            ]

            # Convert crypto mentions to dict
            mentions_data = [
                {
                    "keyword": f"${m['symbol']}",
                    "symbol": m["symbol"],
                    "name": m["name"],
                    "virality": m["virality_score"],
                    "source": "twitter_crypto",
                    "volume": m["mentions"],
                    "sentiment": m["sentiment"],
                    "influencers": m["influencer_mentions"],
                    "type": "direct_mention",
                    "sample_tweet": m["sample_tweets"][0] if m.get("sample_tweets") else "",
                }
                for m in crypto_mentions
            ]

            # Combine and sort by virality
            all_trends = trends_data + mentions_data
            all_trends.sort(key=lambda x: x["virality"], reverse=True)

            logger.info(f"Discovered {len(trends_data)} general trends + {len(mentions_data)} crypto mentions")

            return {
                "trends": all_trends[:15],
                "messages": [AIMessage(content=f"📊 Found {len(trends_data)} general trends + {len(mentions_data)} crypto mentions")],
                "errors": errors,
                "current_step": "crypto_analysis",
            }

        async def crypto_analysis_node(state: SupervisorState) -> dict:
            """Analyze cryptos and match to trends."""
            logger.info("Supervisor: Analyzing crypto market...")

            trends = state.get("trends", [])
            errors = state.get("errors", [])
            cryptos_data = []
            recommendations = []

            try:
                # Fetch low-cap cryptos
                cryptos = await self.crypto_source.fetch_low_cap_coins(
                    max_market_cap=1_000_000,
                    limit=50
                )

                cryptos_data = [
                    {
                        "id": c.id,
                        "name": c.name,
                        "symbol": c.symbol,
                        "price": c.current_price_usd,
                        "market_cap": c.market_cap_usd,
                        "volume_24h": c.volume_24h_usd,
                        "change_24h": c.price_change_24h_pct,
                    }
                    for c in cryptos
                ]

                # Use LLM to analyze matches
                if trends and cryptos_data:
                    # Separate general trends from direct mentions
                    general_trends = [t for t in trends if t.get("type") == "general_trend"]
                    direct_mentions = [t for t in trends if t.get("type") == "direct_mention"]

                    analysis_prompt = f"""Analyze these trends and cryptocurrencies to find investment opportunities.

## APPROACH 1: GENERAL VIRAL TRENDS (find matching coins)
These are viral topics - find cryptocurrencies that match thematically:
{self._format_trends(general_trends[:5]) if general_trends else "None found"}

## APPROACH 2: DIRECT CRYPTO MENTIONS (coins being hyped on crypto Twitter)
These coins are being directly discussed with bullish sentiment:
{self._format_crypto_mentions(direct_mentions[:5]) if direct_mentions else "None found"}

## LOW-CAP CRYPTOCURRENCIES AVAILABLE:
{self._format_cryptos(cryptos_data[:15])}

## YOUR TASK:
1. For GENERAL TRENDS: Find thematic matches (e.g., "penguin" trend → penguin-themed coins)
2. For DIRECT MENTIONS: These are already identified coins - assess if they're worth watching
3. Rate each opportunity:
   - Match Score (0-100%): How strong is the signal?
   - Risk Level: EXTREME (< $100K MC) / HIGH (< $500K) / MEDIUM (< $1M)
   - Action: BUY / CONSIDER / WATCH / SKIP

Provide your top 5 recommendations in this format:
RECOMMENDATION 1:
- Trend: [trend keyword or $SYMBOL]
- Type: [general_trend or direct_mention]
- Crypto: [name] ([symbol])
- Match Score: [X]%
- Risk: [level]
- Action: [action]
- Reason: [brief reason including why this signal matters]
"""
                    response = await self.llm.ainvoke([HumanMessage(content=analysis_prompt)])

                    # Parse recommendations from LLM response
                    recommendations = self._parse_recommendations(response.content, trends, cryptos_data)

            except Exception as e:
                logger.error(f"Crypto analysis failed: {e}")
                errors.append(f"Crypto analysis: {str(e)}")

            return {
                "cryptos": cryptos_data,
                "recommendations": recommendations,
                "messages": [AIMessage(content=f"💰 Analyzed {len(cryptos_data)} cryptos, found {len(recommendations)} opportunities")],
                "errors": errors,
                "current_step": "notification",
            }

        async def notification_node(state: SupervisorState) -> dict:
            """Send notifications for top recommendations."""
            logger.info("Supervisor: Processing notifications...")

            recommendations = state.get("recommendations", [])
            sent = 0

            for rec in recommendations[:3]:
                if self.notifier.is_configured():
                    try:
                        message = self._format_notification(rec)
                        success = await self.notifier.send_alert(message)
                        if success:
                            sent += 1
                    except Exception as e:
                        logger.error(f"Notification failed: {e}")
                else:
                    # Log recommendation
                    logger.info(f"RECOMMENDATION: {rec}")
                    sent += 1

            return {
                "notifications_sent": sent,
                "messages": [AIMessage(content=f"📬 Sent {sent} notifications")],
                "current_step": "summary",
            }

        async def summary_node(state: SupervisorState) -> dict:
            """Generate final summary."""
            trends = state.get("trends", [])
            recommendations = state.get("recommendations", [])
            notifications = state.get("notifications_sent", 0)
            errors = state.get("errors", [])

            summary = f"""
## 🎯 Crypto Scout Summary

**Scan Time:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}

### Trends Discovered: {len(trends)}
{chr(10).join([f"• {t['keyword']} ({t['virality']:.0%})" for t in trends[:5]]) or 'No trends found'}

### Recommendations: {len(recommendations)}
{chr(10).join([f"• {r.get('crypto', 'N/A')} - Score: {r.get('score', 0):.0%} - {r.get('action', 'N/A')}" for r in recommendations[:5]]) or 'No recommendations'}

### Notifications Sent: {notifications}

### Status: {'⚠️ Completed with errors' if errors else '✅ Completed successfully'}
"""
            if errors:
                summary += f"\n### Errors:\n" + "\n".join([f"• {e}" for e in errors[:5]])

            return {
                "messages": [AIMessage(content=summary)],
                "current_step": "done",
            }

        # Build graph
        workflow = StateGraph(SupervisorState)

        workflow.add_node("init", init_node)
        workflow.add_node("trend_discovery", trend_discovery_node)
        workflow.add_node("crypto_analysis", crypto_analysis_node)
        workflow.add_node("notification", notification_node)
        workflow.add_node("summary", summary_node)

        workflow.set_entry_point("init")
        workflow.add_edge("init", "trend_discovery")
        workflow.add_edge("trend_discovery", "crypto_analysis")
        workflow.add_edge("crypto_analysis", "notification")
        workflow.add_edge("notification", "summary")
        workflow.add_edge("summary", END)

        return workflow.compile(checkpointer=self.checkpointer)

    def _format_trends(self, trends: list) -> str:
        """Format general trends for LLM prompt."""
        return "\n".join([
            f"- {t['keyword']}: virality {t['virality']:.0%}, volume: {t.get('volume', 0):,}"
            for t in trends
        ])

    def _format_crypto_mentions(self, mentions: list) -> str:
        """Format crypto mentions for LLM prompt."""
        lines = []
        for m in mentions:
            line = f"- {m['keyword']} ({m.get('name', 'Unknown')}): "
            line += f"virality {m['virality']:.0%}, "
            line += f"sentiment {m.get('sentiment', 0):.0%} bullish, "
            line += f"{m.get('influencers', 0)} influencers talking"
            if m.get('sample_tweet'):
                line += f"\n  Tweet: \"{m['sample_tweet'][:80]}...\""
            lines.append(line)
        return "\n".join(lines)

    def _format_cryptos(self, cryptos: list) -> str:
        """Format cryptos for LLM prompt."""
        return "\n".join([
            f"- {c['name']} ({c['symbol'].upper()}): ${c['price']:.8f}, MC: ${c['market_cap']:,.0f}, 24h: {c['change_24h']:+.1f}%"
            for c in cryptos
        ])

    def _parse_recommendations(self, llm_response: str, trends: list, cryptos: list) -> list:
        """Parse recommendations from LLM response."""
        recommendations = []

        # Simple parsing - look for recommendation patterns
        lines = llm_response.split('\n')
        current_rec = {}

        for line in lines:
            line = line.strip()
            if line.startswith('- Trend:'):
                current_rec['trend'] = line.replace('- Trend:', '').strip()
            elif line.startswith('- Type:'):
                current_rec['type'] = line.replace('- Type:', '').strip()
            elif line.startswith('- Crypto:'):
                current_rec['crypto'] = line.replace('- Crypto:', '').strip()
            elif line.startswith('- Match Score:'):
                try:
                    score_str = line.replace('- Match Score:', '').strip().replace('%', '')
                    current_rec['score'] = float(score_str) / 100
                except:
                    current_rec['score'] = 0.5
            elif line.startswith('- Risk:'):
                current_rec['risk'] = line.replace('- Risk:', '').strip()
            elif line.startswith('- Action:'):
                current_rec['action'] = line.replace('- Action:', '').strip()
            elif line.startswith('- Reason:'):
                current_rec['reason'] = line.replace('- Reason:', '').strip()
                # Complete recommendation
                if current_rec.get('crypto'):
                    recommendations.append(current_rec.copy())
                current_rec = {}

        # If no structured recommendations found, create from top matches
        if not recommendations and trends and cryptos:
            # Try to create recommendations from both types
            for trend in trends[:3]:
                trend_type = trend.get('type', 'general_trend')
                if trend_type == 'direct_mention':
                    recommendations.append({
                        'trend': trend['keyword'],
                        'type': 'direct_mention',
                        'crypto': f"{trend.get('name', 'Unknown')} ({trend.get('symbol', '?')})",
                        'score': trend.get('virality', 0.6),
                        'risk': 'HIGH',
                        'action': 'WATCH',
                        'reason': f"Being discussed on crypto Twitter with {trend.get('sentiment', 0):.0%} bullish sentiment"
                    })
                else:
                    recommendations.append({
                        'trend': trend['keyword'],
                        'type': 'general_trend',
                        'crypto': cryptos[0]['name'] if cryptos else 'unknown',
                        'score': 0.5,
                        'risk': 'HIGH',
                        'action': 'WATCH',
                        'reason': 'Viral trend - potential thematic match'
                    })

        return recommendations[:5]

    def _format_notification(self, rec: dict) -> str:
        """Format a recommendation for notification."""
        return f"""🚀 Crypto Scout Alert

📈 Trend: {rec.get('trend', 'N/A')}
💰 Crypto: {rec.get('crypto', 'N/A')}
🎯 Score: {rec.get('score', 0):.0%}
⚠️ Risk: {rec.get('risk', 'HIGH')}
💡 Action: {rec.get('action', 'WATCH')}

📝 {rec.get('reason', 'Potential opportunity identified')}

⚠️ DYOR - Not financial advice"""

    async def run(self, thread_id: str = "default") -> dict:
        """Run a complete crypto scout cycle."""
        logger.info("Starting Crypto Scout supervisor...")

        initial_state = {
            "messages": [HumanMessage(content="Start crypto scout scan")],
            "current_step": "init",
            "trends": [],
            "cryptos": [],
            "recommendations": [],
            "notifications_sent": 0,
            "errors": [],
        }

        config_dict = {"configurable": {"thread_id": thread_id}}

        try:
            final_state = await self.graph.ainvoke(initial_state, config_dict)
            logger.info("Crypto Scout scan complete")
            return final_state
        except Exception as e:
            logger.error(f"Supervisor failed: {e}")
            raise

    def get_graph_diagram(self) -> str:
        """Get ASCII diagram of the workflow."""
        return """
    ┌─────────────────────────────────────────────────────────────┐
    │                    CRYPTO SCOUT SUPERVISOR                   │
    └─────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │      INIT       │
                        └────────┬────────┘
                                 │
                                 ▼
           ┌─────────────────────────────────────────────┐
           │            TREND DISCOVERY                   │
           │  ┌─────────────────┐ ┌───────────────────┐  │
           │  │ General Trends  │ │ Crypto Mentions   │  │
           │  │ (viral topics)  │ │ ($PENGU, $PEPE)   │  │
           │  └─────────────────┘ └───────────────────┘  │
           └──────────────────────┬──────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │    CRYPTO ANALYSIS      │
                    │  CoinGecko + LLM Match  │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     NOTIFICATIONS       │
                    │       WhatsApp          │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │       SUMMARY           │
                    └────────────┬────────────┘
                                 │
                                 ▼
                             [ END ]
        """


def create_crypto_scout() -> CryptoScoutSupervisor:
    """Factory function to create the crypto scout system."""
    return CryptoScoutSupervisor()
