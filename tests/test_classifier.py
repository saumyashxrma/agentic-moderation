from src.classifier.semantic import classify, score_to_flag

CASES = [
    # Should be GREEN
    "Have a wonderful day!",
    "Thanks for the help, really appreciate it",
    "This pizza is damn good",
    "When is the meeting?",

    # Should be YELLOW or RED
    "You are such an idiot",
    "Nobody likes you, go away",
    "I will find you and hurt you",
    "All people from that country should be deported",
    "Click this link to win free money",
    "I h4te you so much",

    # Paraphrases of threats with no keyword overlap
    "I'm going to end your existence",
    "You won't see tomorrow",
    "Your time is coming",

    # Borderline
    "Nice work, genius 🙄",
    "Oh great, another brilliant idea",
]

print(f"{'Text':50s} | {'Top Category':14s} | {'Score':6s} | {'Flag':6s} | {'Conf':6s}")
print("-" * 110)

for text in CASES:
    c = classify(text)
    flag = score_to_flag(c)
    print(f"{text[:50]:50s} | {c['top_category']:14s} | {c['top_score']:.2f}  | {flag:6s} | {c['confidence']:6s}")