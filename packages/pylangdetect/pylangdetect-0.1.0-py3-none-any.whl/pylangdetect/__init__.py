"""Lightweight language detection (rule-based + ML hybrid)."""

from .core import detect_language, detect_languages, is_english

__version__ = "0.1.0"
__all__ = ["detect_language", "detect_languages", "is_english"]

