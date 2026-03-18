"""LLM provider factory — returns the first configured provider."""

import config
from langchain_core.language_models import BaseChatModel


def get_llm(temperature: float = 0.3) -> BaseChatModel:
    """Return a configured LLM instance using the first available API key."""

    if config.GROQ_API_KEY:
        from langchain_groq import ChatGroq
        return ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=config.GROQ_API_KEY,
            temperature=temperature,
        )

    if config.GOOGLE_API_KEY:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=config.GOOGLE_API_KEY,
            temperature=temperature,
        )

    if config.ANTHROPIC_API_KEY:
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=config.ANTHROPIC_API_KEY,
            temperature=temperature,
            max_tokens=2048,
        )

    if config.OPENAI_API_KEY:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="gpt-4-turbo-preview",
            api_key=config.OPENAI_API_KEY,
            temperature=temperature,
        )

    raise ValueError(
        "No LLM API key found. Set one of: "
        "GROQ_API_KEY, GOOGLE_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY"
    )
