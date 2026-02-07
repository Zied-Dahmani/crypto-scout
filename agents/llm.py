"""
LLM configuration and factory for agents.
"""

import os
from typing import Optional

from langchain_core.language_models import BaseChatModel

from config.settings import config
from utils.logger import get_logger

logger = get_logger(__name__)


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.3
) -> BaseChatModel:
    """
    Get a configured LLM instance.

    Args:
        provider: 'groq', 'openai', 'anthropic', or 'gemini'
        model: Model name override
        temperature: Sampling temperature

    Returns:
        Configured LLM instance
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")

    # Groq (preferred - fast and free)
    if groq_api_key:
        from langchain_groq import ChatGroq

        model_name = model or "llama-3.3-70b-versatile"
        logger.info(f"Initializing Groq LLM: {model_name}")

        return ChatGroq(
            model=model_name,
            api_key=groq_api_key,
            temperature=temperature,
        )

    # Gemini / Google
    elif google_api_key:
        from langchain_google_genai import ChatGoogleGenerativeAI

        model_name = model or "gemini-2.0-flash"
        logger.info(f"Initializing Gemini LLM: {model_name}")

        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=google_api_key,
            temperature=temperature,
        )

    # Anthropic
    elif config.llm.anthropic_api_key:
        from langchain_anthropic import ChatAnthropic

        model_name = model or "claude-sonnet-4-20250514"
        logger.info(f"Initializing Anthropic LLM: {model_name}")

        return ChatAnthropic(
            model=model_name,
            api_key=config.llm.anthropic_api_key,
            temperature=temperature,
            max_tokens=4096,
        )

    # OpenAI
    elif config.llm.openai_api_key:
        from langchain_openai import ChatOpenAI

        model_name = model or config.llm.model_name or "gpt-4-turbo-preview"
        logger.info(f"Initializing OpenAI LLM: {model_name}")

        return ChatOpenAI(
            model=model_name,
            api_key=config.llm.openai_api_key,
            temperature=temperature,
        )

    else:
        raise ValueError(
            "No LLM API key configured. Set one of: "
            "GROQ_API_KEY, GOOGLE_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY"
        )


def get_llm_with_tools(tools: list, **kwargs) -> BaseChatModel:
    """
    Get an LLM instance with tools bound.

    Args:
        tools: List of tools to bind
        **kwargs: Additional arguments for get_llm

    Returns:
        LLM with tools bound
    """
    llm = get_llm(**kwargs)
    return llm.bind_tools(tools)
