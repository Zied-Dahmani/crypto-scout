"""
Trend Discovery Agent - LLM-powered agent for viral trend detection.
"""

from typing import Annotated, Sequence, TypedDict, Literal
import operator

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from .llm import get_llm_with_tools
from .tools.trend_tools import TREND_TOOLS
from utils.logger import get_logger

logger = get_logger(__name__)


# Agent system prompt
TREND_AGENT_PROMPT = """You are an expert social media trend analyst specializing in cryptocurrency and viral topics.

Your mission is to discover and analyze viral trends that could signal emerging cryptocurrency opportunities.

## Your Capabilities
You have access to tools that let you:
1. Discover trending topics from Twitter/X
2. Discover trending topics from Reddit crypto communities
3. Search for specific topics across platforms

## Your Process
1. First, scan Twitter for viral crypto-related trends
2. Then, scan Reddit crypto communities for hot topics
3. For interesting trends, search deeper to understand the topic
4. Identify trends with high virality and growth potential

## What Makes a Good Trend
- High engagement and rapid growth
- Clear thematic connection (memes, animals, cultural references)
- Cross-platform presence (trending on multiple platforms)
- Positive or neutral sentiment
- Not already oversaturated

## Output Format
After your analysis, provide a structured summary:
1. Top 3-5 trending topics
2. Virality score for each (0-100%)
3. Brief description of why it's trending
4. Potential crypto connection (if any obvious)

Be thorough but efficient. Focus on actionable trends that could translate to crypto opportunities."""


class TrendAgentState(TypedDict):
    """State for the trend discovery agent."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    discovered_trends: list[dict]


def should_continue(state: TrendAgentState) -> Literal["tools", "end"]:
    """Determine if the agent should continue using tools or end."""
    messages = state["messages"]
    last_message = messages[-1]

    # If LLM made tool calls, continue to tool node
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    # Otherwise, end
    return "end"


def create_trend_agent():
    """
    Create the LangGraph trend discovery agent.

    Returns:
        Compiled LangGraph agent
    """
    # Get LLM with tools
    llm = get_llm_with_tools(TREND_TOOLS)

    # Create the agent node
    async def agent_node(state: TrendAgentState) -> dict:
        """The main agent reasoning node."""
        messages = state["messages"]

        # Add system prompt if not present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=TREND_AGENT_PROMPT)] + list(messages)

        # Call the LLM
        response = await llm.ainvoke(messages)

        return {"messages": [response]}

    # Create the tool node
    tool_node = ToolNode(TREND_TOOLS)

    # Build the graph
    workflow = StateGraph(TrendAgentState)

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


async def run_trend_discovery(user_request: str = None) -> dict:
    """
    Run the trend discovery agent.

    Args:
        user_request: Optional specific request (default: general scan)

    Returns:
        Final state with discovered trends
    """
    agent = create_trend_agent()

    # Default request
    if not user_request:
        user_request = """Please scan for viral trends right now:
1. Check Twitter for trending crypto topics
2. Check Reddit crypto communities for hot discussions
3. Identify the top 5 most viral trends
4. Provide virality scores and brief analysis for each"""

    initial_state = {
        "messages": [HumanMessage(content=user_request)],
        "discovered_trends": [],
    }

    logger.info("Starting trend discovery agent...")

    final_state = await agent.ainvoke(initial_state)

    logger.info("Trend discovery complete")

    return final_state
