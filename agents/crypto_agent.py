"""
Crypto Analysis Agent - LLM-powered agent for cryptocurrency analysis.
"""

from typing import Annotated, Sequence, TypedDict, Literal
import operator

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from .llm import get_llm_with_tools
from .tools.crypto_tools import CRYPTO_TOOLS
from .tools.analysis_tools import ANALYSIS_TOOLS
from utils.logger import get_logger

logger = get_logger(__name__)


# Combined tools for crypto agent
CRYPTO_AGENT_TOOLS = CRYPTO_TOOLS + ANALYSIS_TOOLS


# Agent system prompt
CRYPTO_AGENT_PROMPT = """You are an expert cryptocurrency analyst specializing in low-cap altcoins and memecoins.

Your mission is to analyze trending topics and find matching low-cap cryptocurrencies with high upside potential.

## Your Capabilities
You have access to tools that let you:
1. Fetch low market cap cryptocurrencies (< $1 million)
2. Search for cryptocurrencies by name/keyword
3. Get detailed information about specific coins
4. Analyze trend-crypto matches
5. Calculate investment scores
6. Generate structured recommendations

## Your Process
When given a trending topic:
1. Search for cryptocurrencies that match the trend keyword
2. Also scan general low-cap coins for potential matches
3. Get detailed info on promising candidates
4. Analyze the match between trend and crypto
5. Calculate investment scores
6. Generate recommendations for the best opportunities

## What Makes a Good Opportunity
- Strong keyword/thematic match to the trend
- Market cap under $1 million (more upside potential)
- Decent trading volume (liquidity for entry/exit)
- Positive price momentum
- Clear project identity and community

## Risk Assessment
Always consider:
- Micro-caps are EXTREMELY risky
- Low liquidity can trap investors
- Memecoins can go to zero overnight
- Only invest what you can lose completely

## Output Format
For each opportunity found:
1. Crypto name and symbol
2. Match score (0-100%)
3. Investment score (0-100%)
4. Risk level (EXTREME/VERY HIGH/HIGH/MEDIUM)
5. Suggested action (BUY/CONSIDER/WATCH/SKIP)
6. Key reasons for the recommendation

Be thorough, analytical, and always emphasize the risks involved."""


class CryptoAgentState(TypedDict):
    """State for the crypto analysis agent."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    trends_to_analyze: list[dict]
    recommendations: list[dict]


def should_continue(state: CryptoAgentState) -> Literal["tools", "end"]:
    """Determine if the agent should continue using tools or end."""
    messages = state["messages"]
    last_message = messages[-1]

    # If LLM made tool calls, continue to tool node
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    # Otherwise, end
    return "end"


def create_crypto_agent():
    """
    Create the LangGraph crypto analysis agent.

    Returns:
        Compiled LangGraph agent
    """
    # Get LLM with tools
    llm = get_llm_with_tools(CRYPTO_AGENT_TOOLS)

    # Create the agent node
    async def agent_node(state: CryptoAgentState) -> dict:
        """The main agent reasoning node."""
        messages = state["messages"]

        # Add system prompt if not present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=CRYPTO_AGENT_PROMPT)] + list(messages)

        # Call the LLM
        response = await llm.ainvoke(messages)

        return {"messages": [response]}

    # Create the tool node
    tool_node = ToolNode(CRYPTO_AGENT_TOOLS)

    # Build the graph
    workflow = StateGraph(CryptoAgentState)

    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)

    # Set entry point
    workflow.set_entry_point("agent")

    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        }
    )

    # Tools always go back to agent
    workflow.add_edge("tools", "agent")

    # Compile
    return workflow.compile()


async def run_crypto_analysis(trends: list[dict] = None, user_request: str = None) -> dict:
    """
    Run the crypto analysis agent.

    Args:
        trends: List of trends to analyze (optional)
        user_request: Optional specific request

    Returns:
        Final state with recommendations
    """
    agent = create_crypto_agent()

    # Build request based on trends
    if trends:
        trends_text = "\n".join([
            f"- {t.get('keyword', t.get('name', 'unknown'))} "
            f"(virality: {t.get('virality_score', t.get('virality', 0)):.0%})"
            for t in trends[:5]
        ])
        request = f"""Analyze these trending topics and find matching cryptocurrencies:

{trends_text}

For each trend:
1. Search for related cryptocurrencies
2. Analyze the matches
3. Calculate investment scores
4. Generate recommendations for the best opportunities"""

    elif user_request:
        request = user_request
    else:
        request = """Scan the low-cap crypto market for opportunities:
1. Fetch low market cap cryptocurrencies
2. Identify interesting projects
3. Analyze their potential
4. Provide recommendations"""

    initial_state = {
        "messages": [HumanMessage(content=request)],
        "trends_to_analyze": trends or [],
        "recommendations": [],
    }

    logger.info("Starting crypto analysis agent...")

    final_state = await agent.ainvoke(initial_state)

    logger.info("Crypto analysis complete")

    return final_state
