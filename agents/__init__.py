"""
LangGraph AI Agents module.

This module provides LLM-powered agents for crypto trend discovery and analysis.
"""

from .llm import get_llm, get_llm_with_tools
from .trend_agent import create_trend_agent, run_trend_discovery
from .crypto_agent import create_crypto_agent, run_crypto_analysis
from .supervisor import CryptoScoutSupervisor, create_crypto_scout

__all__ = [
    # LLM utilities
    "get_llm",
    "get_llm_with_tools",
    # Individual agents
    "create_trend_agent",
    "create_crypto_agent",
    "run_trend_discovery",
    "run_crypto_analysis",
    # Supervisor
    "CryptoScoutSupervisor",
    "create_crypto_scout",
]
