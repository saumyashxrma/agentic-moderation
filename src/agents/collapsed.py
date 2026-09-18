"""
Tiered moderation:
- Tier 1: embedding classifier (~50ms, no LLM)
- Tier 2: LLM escalation for ambiguous cases (~5s)
"""
import time
from strands import Agent
from strands.models.ollama import OllamaModel

from src.config import config
from src.classifier.semantic import classify, score_to_flag
from src.agents.parser import parse_with_retry
from src.agents.prompts import MODERATION_SYSTEM_PROMPT
from src.ingestion.normalizer import normalize_text

# Module-level caches so we build these once
_llm_agent = None


def _get_llm_agent():
    """Build the Strands agent once and reuse it."""
    global _llm_agent
    if _llm_agent is None:
        model = OllamaModel(
            host=config.OLLAMA_HOST,
            model_id=config.OLLAMA_MODEL,
            keep_alive=-1,  # never unload during demo window
            temperature=0.1,
        )
        _llm_agent = Agent(
            model=model,
            system_prompt=MODERATION_SYSTEM_PROMPT,
            callback_handler=None,
        )
    return _llm_agent


def _empty_result():
    return {
        "flag": "YELLOW",
        "tone": "unknown",
        "violation": False,
        "category": None,
        "reason": "Empty input, needs review",
        "tier_used": "none",
        "tier1_score": 0.0,
    }


def moderate_tiered(text: str) -> dict:
    """
    Two-tier moderation.

    1. Run embedding classifier.
    2. If high confidence → return immediately (Tier 1).
    3. If medium/low confidence → escalate to LLM (Tier 2).

    Always returns a dict with keys:
        flag, tone, violation, category, reason, tier_used, tier1_score
    """
    if not text or not text.strip():
        return _empty_result()

    start = time.time()

    # ---------- TIER 1: Embedding classifier ----------
    c = classify(text)
    tier1_flag = score_to_flag(c)
    tier1_conf = c["confidence"]

    if tier1_conf in ("high", "medium"):
        return {
            "flag": tier1_flag,
            "tone": "unknown",
            "violation": tier1_flag in ("YELLOW", "RED"),
            "category": c["top_category"] if tier1_flag != "GREEN" else None,
            "reason": f"Tier1 semantic match: {c['top_category']} ({c['top_score']:.2f})",
            "tier_used": "embedding",
            "tier1_score": c["top_score"],
            "latency_s": round(time.time() - start, 3),
        }

    # ---------- TIER 2: LLM escalation ----------
    agent = _get_llm_agent()
    normalized = normalize_text(text)[:2000]
    raw = str(agent(normalized))
    result = parse_with_retry(raw, agent, text)

    result["tier_used"] = "llm"
    result["tier1_score"] = c["top_score"]
    result["tier1_category"] = c["top_category"]
    result["latency_s"] = round(time.time() - start, 3)
    return result