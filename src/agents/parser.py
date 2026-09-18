import json
import re
from pydantic import BaseModel, ValidationError
from typing import Optional


class ModerationResult(BaseModel):
    flag: str
    tone: Optional[str] = "unknown"
    violation: Optional[bool] = False
    category: Optional[str] = None
    reason: str = ""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        return cls(**v) if isinstance(v, dict) else v


def _extract_json_block(text: str):
    """Find the first balanced {...} block, respecting nesting."""
    if not text:
        return None
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                return text[start:i + 1]
    return None


def _normalize_flag(value) -> str:
    v = str(value or "").strip().upper()
    if v in ("GREEN", "YELLOW", "RED"):
        return v
    return "YELLOW"


def parse_flag(raw) -> dict:
    """
    Parse a model response into a validated dict.
    Never raises — always returns a valid shape.
    """
    if raw is None:
        return _fail_safe("Empty response")

    text = str(raw).strip()

    # Attempt 1: direct parse
    for candidate in (text, _extract_json_block(text)):
        if not candidate:
            continue
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                return {
                    "flag": _normalize_flag(obj.get("flag")),
                    "tone": str(obj.get("tone") or "unknown"),
                    "violation": bool(obj.get("violation", False)),
                    "category": obj.get("category"),
                    "reason": str(obj.get("reason") or "")[:300],
                }
        except (json.JSONDecodeError, TypeError):
            continue

    # Attempt 2: regex flag extraction
    m = re.search(r"\b(GREEN|YELLOW|RED)\b", text.upper())
    if m:
        return {
            "flag": m.group(1),
            "tone": "unknown",
            "violation": False,
            "category": None,
            "reason": text[:200] or "Recovered from malformed output",
        }

    return _fail_safe("Needs human review: unparseable model output")


def parse_with_retry(raw, agent, original_text, max_retries=2) -> dict:
    """
    If parsing fails, send the malformed output back to the model for correction.
    Falls back to the fail-safe if retries are exhausted.
    """
    result = parse_flag(raw)
    if "Needs human review" not in result.get("reason", ""):
        return result

    for attempt in range(max_retries):
        correction_prompt = f"""Your previous response was not valid JSON. Fix it.

Original input: {original_text[:500]}
Your previous response: {str(raw)[:500]}

Return ONLY a valid JSON object matching this schema:
{{"flag": "GREEN|YELLOW|RED", "tone": "string", "violation": true|false, "category": "string or null", "reason": "string"}}

No prose. No markdown. Just the JSON object.
"""
        try:
            new_raw = str(agent(correction_prompt))
            retry_result = parse_flag(new_raw)
            if "Needs human review" not in retry_result.get("reason", ""):
                retry_result["reason"] = f"{retry_result['reason']} (corrected on retry {attempt + 1})"
                return retry_result
        except Exception:
            continue

    return result


def _fail_safe(reason: str) -> dict:
    return {
        "flag": "YELLOW",
        "tone": "unknown",
        "violation": False,
        "category": None,
        "reason": reason,
    }