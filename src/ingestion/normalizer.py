import re
import hashlib


_WHITESPACE_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s]")

# Leetspeak → canonical letter substitution.
# Order matters: this runs BEFORE punctuation stripping,
# so we can catch @ → a, $ → s, etc. that would otherwise be removed.
_LEET_MAP = {
    "4": "a", "@": "a", "8": "b",
    "(": "c", "{": "c", "<": "c",
    "3": "e", "6": "g", "9": "g",
    "1": "i", "!": "i", "|": "i",
    "0": "o", "$": "s", "5": "s",
    "7": "t", "+": "t",
    "2": "z",
}


def deleet(text: str) -> str:
    """Map leetspeak characters to their canonical letters."""
    return "".join(_LEET_MAP.get(ch, ch) for ch in text.lower())


def normalize_text(text: str, strip_punct: bool = True) -> str:
    """
    Full normalization pipeline:
    1. Lowercase
    2. De-leet (h4te → hate, @ → a, etc.)
    3. Strip punctuation (optional)
    4. Collapse whitespace
    """
    text = text.lower()
    text = deleet(text)
    if strip_punct:
        text = _PUNCT_RE.sub("", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text


def text_cache_key(text: str) -> str:
    """Stable cache key for a normalized text string."""
    normalized = normalize_text(text)
    return f"text:{hashlib.sha256(normalized.encode()).hexdigest()}"