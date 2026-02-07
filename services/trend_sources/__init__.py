"""Trend sources module."""

from .base import BaseTrendSource
from .twitter import TwitterTrendSource
from .reddit import RedditTrendSource

__all__ = [
    "BaseTrendSource",
    "TwitterTrendSource",
    "RedditTrendSource",
]
