"""Core language detection functions."""

import re
from typing import List, Tuple


# Common words for language detection
LANGUAGE_WORDS = {
    "en": {"the", "be", "to", "of", "and", "a", "in", "that", "have", "i"},
    "es": {"el", "la", "de", "que", "y", "a", "en", "un", "ser", "se"},
    "fr": {"le", "de", "et", "à", "un", "il", "être", "et", "en", "avoir"},
    "de": {"der", "die", "und", "in", "den", "von", "zu", "das", "mit", "sich"},
}


def detect_language(text: str) -> str:
    """Detect the most likely language."""
    text_lower = text.lower()
    words = set(re.findall(r"\b\w+\b", text_lower))
    
    scores = {}
    for lang, common_words in LANGUAGE_WORDS.items():
        score = len(words.intersection(common_words))
        scores[lang] = score
    
    if not scores or max(scores.values()) == 0:
        return "unknown"
    
    return max(scores.items(), key=lambda x: x[1])[0]


def detect_languages(text: str, top_n: int = 3) -> List[Tuple[str, float]]:
    """Detect top N languages with confidence scores."""
    text_lower = text.lower()
    words = set(re.findall(r"\b\w+\b", text_lower))
    
    scores = {}
    for lang, common_words in LANGUAGE_WORDS.items():
        score = len(words.intersection(common_words))
        scores[lang] = score
    
    total = sum(scores.values())
    if total == 0:
        return [("unknown", 0.0)]
    
    normalized = [(lang, score / total) for lang, score in scores.items()]
    sorted_scores = sorted(normalized, key=lambda x: x[1], reverse=True)
    return sorted_scores[:top_n]


def is_english(text: str) -> bool:
    """Check if text is English."""
    return detect_language(text) == "en"

