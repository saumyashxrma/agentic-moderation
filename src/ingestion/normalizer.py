import re
import hashlib

_WHITESPACE_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s]")

def normalize_text(text: str) -> str:
    text = text.lower()
    text = _PUNCT_RE.sub("", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text

def text_cache_key(text: str) -> str:
    normalized = normalize_text(text)
    return f"text:{hashlib.sha256(normalized.encode()).hexdigest()}"