"""
Trend-to-crypto matching and scoring service.
"""

import hashlib
import re
from datetime import datetime, timezone
from typing import Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from models.trend import Trend
from models.cryptocurrency import Cryptocurrency
from models.match import MatchResult
from models.recommendation import Recommendation
from utils.logger import get_logger

logger = get_logger(__name__)


class MatchingService:
    """Service for matching trends to cryptocurrencies."""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            max_features=1000,
        )

    def match_trends_to_cryptos(
        self,
        trends: list[Trend],
        cryptos: list[Cryptocurrency],
        min_score: float = 0.1
    ) -> list[MatchResult]:
        """
        Match trending topics to cryptocurrencies.

        Args:
            trends: List of detected trends
            cryptos: List of cryptocurrencies to match against
            min_score: Minimum match score threshold

        Returns:
            List of MatchResult objects
        """
        matches = []

        for trend in trends:
            for crypto in cryptos:
                match_result = self._calculate_match(trend, crypto)

                if match_result and match_result.match_score >= min_score:
                    matches.append(match_result)

        # Sort by match score descending
        matches.sort(key=lambda x: x.match_score, reverse=True)

        logger.info(f"Found {len(matches)} trend-crypto matches")
        return matches

    def _calculate_match(
        self,
        trend: Trend,
        crypto: Cryptocurrency
    ) -> Optional[MatchResult]:
        """Calculate match score between a trend and cryptocurrency."""
        keyword_score, keyword_matches = self._keyword_match_score(trend, crypto)
        semantic_score = self._semantic_similarity_score(trend, crypto)

        # Weighted combination
        match_score = 0.7 * keyword_score + 0.3 * semantic_score

        if match_score < 0.05:
            return None

        # Build match reasons
        reasons = []
        if keyword_score > 0.3:
            reasons.append(f"Strong keyword match: {', '.join(keyword_matches[:3])}")
        if semantic_score > 0.2:
            reasons.append("Semantic similarity in descriptions")
        if trend.virality_score > 0.7:
            reasons.append(f"High virality trend ({trend.virality_score:.0%})")
        if crypto.price_change_24h_pct > 20:
            reasons.append(f"Strong price momentum (+{crypto.price_change_24h_pct:.1f}%)")

        return MatchResult(
            trend=trend,
            crypto=crypto,
            match_score=min(match_score, 1.0),
            match_reasons=reasons,
            keyword_matches=keyword_matches,
        )

    def _keyword_match_score(
        self,
        trend: Trend,
        crypto: Cryptocurrency
    ) -> tuple[float, list[str]]:
        """Calculate keyword-based match score."""
        trend_keywords = self._extract_keywords_from_trend(trend)
        crypto_keywords = self._extract_keywords_from_crypto(crypto)

        matches = []
        score = 0.0

        for tk in trend_keywords:
            tk_lower = tk.lower()

            # Direct matches
            for ck in crypto_keywords:
                ck_lower = ck.lower()

                if tk_lower == ck_lower:
                    score += 1.0
                    matches.append(tk)
                elif tk_lower in ck_lower or ck_lower in tk_lower:
                    score += 0.5
                    matches.append(f"{tk}~{ck}")

        # Normalize score
        max_possible = max(len(trend_keywords), 1)
        normalized_score = min(score / max_possible, 1.0)

        return normalized_score, list(set(matches))

    def _extract_keywords_from_trend(self, trend: Trend) -> list[str]:
        """Extract searchable keywords from trend."""
        keywords = [trend.keyword]
        keywords.extend(trend.related_keywords)

        # Clean and deduplicate
        cleaned = []
        for kw in keywords:
            clean = re.sub(r'[^a-zA-Z0-9]', '', kw.lower())
            if clean and len(clean) >= 2:
                cleaned.append(clean)

        return list(set(cleaned))

    def _extract_keywords_from_crypto(self, crypto: Cryptocurrency) -> list[str]:
        """Extract searchable keywords from cryptocurrency."""
        keywords = [
            crypto.symbol,
            crypto.name,
        ]

        # Add words from name
        name_words = crypto.name.lower().split()
        keywords.extend(name_words)

        # Add categories
        keywords.extend(crypto.categories)

        # Extract from description
        if crypto.description:
            desc_words = re.findall(r'\b[a-zA-Z]{3,}\b', crypto.description.lower())
            keywords.extend(desc_words[:20])

        # Clean and deduplicate
        cleaned = []
        for kw in keywords:
            clean = re.sub(r'[^a-zA-Z0-9]', '', str(kw).lower())
            if clean and len(clean) >= 2:
                cleaned.append(clean)

        return list(set(cleaned))

    def _semantic_similarity_score(
        self,
        trend: Trend,
        crypto: Cryptocurrency
    ) -> float:
        """Calculate semantic similarity using TF-IDF."""
        # Build text representations
        trend_text = " ".join([
            trend.keyword,
            " ".join(trend.related_keywords),
        ])

        crypto_text = " ".join([
            crypto.name,
            crypto.symbol,
            crypto.description or "",
            " ".join(crypto.categories),
        ])

        if not trend_text.strip() or not crypto_text.strip():
            return 0.0

        try:
            # Fit and transform
            tfidf_matrix = self.vectorizer.fit_transform([trend_text, crypto_text])

            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
            return float(similarity[0][0])

        except Exception as e:
            logger.warning("Semantic similarity calculation failed", error=str(e))
            return 0.0


class RecommendationEngine:
    """Engine for generating investment recommendations."""

    def __init__(self, matching_service: Optional[MatchingService] = None):
        self.matching_service = matching_service or MatchingService()

    def generate_recommendations(
        self,
        matches: list[MatchResult],
        min_confidence: float = 0.3,
        max_recommendations: int = 10
    ) -> list[Recommendation]:
        """
        Generate ranked investment recommendations from matches.

        Args:
            matches: List of trend-crypto matches
            min_confidence: Minimum confidence score threshold
            max_recommendations: Maximum recommendations to return

        Returns:
            List of Recommendation objects
        """
        recommendations = []

        for match in matches:
            confidence = self._calculate_confidence(match)

            if confidence < min_confidence:
                continue

            risk_level = self._assess_risk(match)
            action = self._determine_action(confidence, risk_level)
            reasoning = self._generate_reasoning(match, confidence, risk_level)
            potential = self._estimate_potential(match)

            recommendation = Recommendation(
                id=self._generate_id(match),
                match=match,
                confidence_score=confidence,
                risk_level=risk_level,
                potential_upside=potential,
                reasoning=reasoning,
                action=action,
                created_at=datetime.now(timezone.utc),
            )

            recommendations.append(recommendation)

        # Sort by confidence score
        recommendations.sort(key=lambda x: x.confidence_score, reverse=True)

        logger.info(f"Generated {len(recommendations[:max_recommendations])} recommendations")
        return recommendations[:max_recommendations]

    def _calculate_confidence(self, match: MatchResult) -> float:
        """Calculate overall confidence score for a match."""
        trend = match.trend
        crypto = match.crypto

        # Match quality (40%)
        match_quality = match.match_score * 0.4

        # Trend strength (30%)
        trend_strength = trend.virality_score * 0.3

        # Market indicators (30%)
        volume_score = min(crypto.volume_24h_usd / 100000, 1.0)  # Max at $100k volume
        momentum_score = min(max(crypto.price_change_24h_pct / 50, 0), 1.0)  # Max at +50%
        market_score = (volume_score * 0.5 + momentum_score * 0.5) * 0.3

        confidence = match_quality + trend_strength + market_score
        return min(confidence, 1.0)

    def _assess_risk(self, match: MatchResult) -> str:
        """Assess risk level of the investment."""
        crypto = match.crypto

        # Low-cap coins are inherently high risk
        if crypto.market_cap_usd < 100000:
            return "extreme"
        elif crypto.market_cap_usd < 500000:
            return "high"
        elif crypto.market_cap_usd < 1000000:
            return "medium"
        else:
            return "low"

    def _determine_action(self, confidence: float, risk_level: str) -> str:
        """Determine recommended action."""
        if confidence > 0.7 and risk_level in ["low", "medium"]:
            return "buy"
        elif confidence > 0.5:
            return "consider"
        else:
            return "watch"

    def _generate_reasoning(
        self,
        match: MatchResult,
        confidence: float,
        risk_level: str
    ) -> str:
        """Generate detailed reasoning for the recommendation."""
        trend = match.trend
        crypto = match.crypto

        reasoning_parts = []

        # Trend analysis
        reasoning_parts.append(
            f"The topic '{trend.keyword}' is trending on {trend.source.value} "
            f"with a virality score of {trend.virality_score:.0%}."
        )

        # Match analysis
        if match.match_reasons:
            reasoning_parts.append(
                f"Match factors: {'; '.join(match.match_reasons[:3])}."
            )

        # Crypto analysis
        reasoning_parts.append(
            f"{crypto.name} ({crypto.symbol.upper()}) has a market cap of "
            f"${crypto.market_cap_usd:,.0f} and 24h volume of ${crypto.volume_24h_usd:,.0f}."
        )

        if crypto.price_change_24h_pct != 0:
            direction = "up" if crypto.price_change_24h_pct > 0 else "down"
            reasoning_parts.append(
                f"Price is {direction} {abs(crypto.price_change_24h_pct):.1f}% in 24h."
            )

        # Risk warning
        reasoning_parts.append(
            f"Risk level: {risk_level.upper()}. Low-cap cryptocurrencies are highly "
            "volatile and speculative. Only invest what you can afford to lose."
        )

        return " ".join(reasoning_parts)

    def _estimate_potential(self, match: MatchResult) -> str:
        """Estimate potential upside based on trend and market data."""
        virality = match.trend.virality_score
        market_cap = match.crypto.market_cap_usd

        # Very rough estimation based on market cap room to grow
        if market_cap < 100000 and virality > 0.7:
            return "10x-100x (extremely speculative)"
        elif market_cap < 500000 and virality > 0.5:
            return "5x-20x (highly speculative)"
        elif market_cap < 1000000 and virality > 0.3:
            return "2x-5x (speculative)"
        else:
            return "unknown"

    def _generate_id(self, match: MatchResult) -> str:
        """Generate unique recommendation ID."""
        data = f"{match.trend.id}_{match.crypto.id}_{datetime.now(timezone.utc).timestamp()}"
        return hashlib.md5(data.encode()).hexdigest()[:16]
