"""Tests for pylangdetect core functions."""

from pylangdetect import detect_language, detect_languages, is_english


def test_detect_language():
    assert detect_language("Hello world") == "en"
    assert detect_language("Bonjour le monde") == "fr"


def test_is_english():
    assert is_english("Hello world") is True
    assert is_english("Hola mundo") is False


def test_detect_languages():
    result = detect_languages("Hello world", top_n=2)
    assert len(result) <= 2
    assert result[0][0] in ["en", "fr", "es", "de", "unknown"]

