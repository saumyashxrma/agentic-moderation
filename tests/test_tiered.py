"""
Test the two-tier moderator.

Warms up both tiers first, then measures real latency and correctness.
Run twice: first run warms models, second run gives clean numbers.
"""
import sys
import io

# Force UTF-8 output so redirected files work on Windows
if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import time
from src.agents.collapsed import moderate_tiered


# (text, expected_flag, comment)
CASES = [
    # Clear GREEN — should be Tier 1
    ("Have a wonderful day!", "GREEN", "greeting"),
    ("Thanks for the help, really appreciate it", "GREEN", "thanks"),
    ("When is the meeting?", "GREEN", "question"),
    ("This pizza is damn good", "GREEN", "profanity, non-hostile"),

    # Clear violations — should be Tier 1
    ("I will find you and hurt you", "RED", "explicit threat"),
    ("All people from that country are subhuman", "RED", "hate speech"),
    ("Click this link to win free money", "RED", "spam"),
    ("I h4te you so much", "YELLOW", "leetspeak harassment"),

    # Paraphrased threats — likely Tier 2
    ("I'm going to end your existence", "RED", "no keyword overlap"),
    ("You won't see tomorrow", "RED", "implied threat"),

    # Sarcasm — should escalate to Tier 2
    ("Nice work, genius 🙄", "YELLOW", "sarcasm with emoji"),
    ("Oh great, another brilliant idea", "YELLOW", "sarcastic praise"),

    # Ambiguous
    ("You're such an idiot", "YELLOW", "insult"),
]


def warmup():
    """Force model loading so latency measurements are clean."""
    print("Warming up models (this takes ~10-20s)...")
    start = time.time()
    moderate_tiered("warmup call")
    moderate_tiered("I will find you")  # force LLM path
    print(f"Warm-up complete in {time.time() - start:.2f}s\n")


def main():
    warmup()

    print(f"{'Text':42s} | {'Tier':10s} | {'Flag':6s} | {'Exp':6s} | {'OK':2s} | {'Lat':7s} | Reason")
    print("-" * 150)

    tier1_count = 0
    tier2_count = 0
    tier1_time = 0.0
    tier2_time = 0.0
    correct = 0
    total = len(CASES)

    for text, expected, comment in CASES:
        result = moderate_tiered(text)
        tier = result["tier_used"]
        flag = result["flag"]
        latency = result.get("latency_s", 0.0)
        reason = result.get("reason", "")[:35]

        ok = flag == expected
        if ok:
            correct += 1

        if tier == "embedding":
            tier1_count += 1
            tier1_time += latency
        else:
            tier2_count += 1
            tier2_time += latency

        mark = "OK" if ok else "XX"
        print(f"{text[:42]:42s} | {tier:10s} | {flag:6s} | {expected:6s} | {mark:2s} | {latency:5.2f}s | {reason}")

    print("-" * 150)
    print(f"\nCorrect:  {correct}/{total} ({correct/total*100:.0f}%)")
    print(f"Tier 1:   {tier1_count}/{total} ({tier1_count/total*100:.0f}%)  avg {tier1_time/max(tier1_count,1):.3f}s")
    print(f"Tier 2:   {tier2_count}/{total} ({tier2_count/total*100:.0f}%)  avg {tier2_time/max(tier2_count,1):.2f}s")
    print(f"Speedup:  Tier 1 is {tier2_time/max(tier1_time,0.001):.0f}x faster")


if __name__ == "__main__":
    main()