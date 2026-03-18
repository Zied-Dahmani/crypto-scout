"""LangGraph pipeline: trend-driven crypto opportunity detection."""

from langgraph.graph import END, StateGraph

from pipeline.nodes.market_analyzer import market_analyzer
from pipeline.nodes.scorer import scorer
from pipeline.nodes.token_finder import token_finder
from pipeline.nodes.trend_detector import trend_detector
from pipeline.nodes.trend_validator import trend_validator
from pipeline.nodes.wallet_analyzer import wallet_analyzer
from pipeline.state import PipelineState


def build_pipeline():
    """Build and compile the six-node opportunity detection pipeline.

    Flow:
      trend_detector → trend_validator → token_finder
        → market_analyzer → wallet_analyzer → scorer → END
    """
    graph = StateGraph(PipelineState)

    graph.add_node("trend_detector",  trend_detector)
    graph.add_node("trend_validator", trend_validator)
    graph.add_node("token_finder",    token_finder)
    graph.add_node("market_analyzer", market_analyzer)
    graph.add_node("wallet_analyzer", wallet_analyzer)
    graph.add_node("scorer",          scorer)

    graph.set_entry_point("trend_detector")
    graph.add_edge("trend_detector",  "trend_validator")
    graph.add_edge("trend_validator", "token_finder")
    graph.add_edge("token_finder",    "market_analyzer")
    graph.add_edge("market_analyzer", "wallet_analyzer")
    graph.add_edge("wallet_analyzer", "scorer")
    graph.add_edge("scorer",          END)

    return graph.compile()
