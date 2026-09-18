## 2026-09-17 — Two-tier moderator: final Phase 1 result

Test set: 13 cases (adversarial, includes evasion, sarcasm, paraphrased threats).

Result:
- Overall accuracy: 11/13 (85%)
- Tier 1 (embedding): 8/13 (62%), avg 0.022s
- Tier 2 (LLM): 5/13 (38%), avg 2.63s
- Speedup: 76x (Tier 1 vs Tier 2)

Wins:
- Leetspeak evasion ("I h4te you") correctly flagged YELLOW
- Sarcasm with emoji ("Nice work, genius 🙄") correctly flagged YELLOW
- Paraphrased threat ("I'm going to end your existence") correctly RED

Failures:
- "You won't see tomorrow" → GREEN (expected RED)
- "Oh great, another brilliant idea" → GREEN (expected YELLOW)

Both failures share a root cause: the model defaults to literal reading 
when no conversational context is available. Prompt engineering was iterated 
twice; further gains require context, not more examples.

**Decision:** Accept 85% as the Phase 1 result. Both failure modes are 
architecturally solvable in Phase 2 (context layer). Do NOT overfit the 
prompt to these specific cases.

**Pitch line:** "Prompt engineering alone hit 85%. The remaining failures 
are context-dependent — the same ambiguity a human moderator would face 
without seeing the conversation."