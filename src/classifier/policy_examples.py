"""
Seed examples for each moderation category.
Each category gets 8-10 representative sentences.
The embedding model converts these to a category centroid.
"""

POLICY_EXAMPLES = {
    "hate_speech": [
        "All people from that religion are subhuman",
        "Women shouldn't be allowed to work",
        "Those immigrants are ruining our country and should be deported",
        "I hate everyone from that ethnic group",
        "Gay people are a disease on society",
        "That race is inherently violent and criminal",
        "Disabled people are a burden on the economy",
        "Muslims are all terrorists",
    ],
    "harassment": [
        "You are such an idiot, nobody likes you",
        "Shut up, you worthless piece of trash",
        "You're pathetic and everyone hates you",
        "Kill yourself, loser",
        "You're so stupid I can't believe you exist",
        "No one will ever love you, freak",
        "You deserve to be alone forever",
    ],
    "threat": [
        "I will find you and hurt you",
        "I'm going to kill you",
        "I know where you live and I'm coming",
        "You'll regret ever talking to me",
        "I'll make sure you never speak again",
        "I'm going to destroy your life",
        "Watch your back, you're dead",
    ],
    "sexual": [
        "Explicit sexual content involving adults",
        "Send me nude pictures",
        "I want to have sex with you right now",
        "Explicit sexual descriptions of a person",
    ],
    "spam": [
        "Click this link to win free money now",
        "Buy cheap followers today, DM me",
        "Congratulations, you've won a prize, click here",
        "Free crypto giveaway, act fast",
        "Work from home and earn thousands weekly",
        "Send me your password to verify your account",
    ],
    "illegal": [
        "Here's how to make a bomb at home",
        "Where can I buy illegal drugs",
        "How to hack someone's account",
        "Steps to launder money without getting caught",
        "How to make methamphetamine",
    ],
    "benign": [
        "Have a great day!",
        "Thanks for your help, I really appreciate it",
        "What time does the meeting start?",
        "I loved that movie, the acting was incredible",
        "Can you send me the document when you get a chance?",
        "The weather is beautiful today",
        "Great job on the presentation, very well done",
        "I'm excited about the new project",
        "This pizza is damn good",
        "Let me know if you need anything else",
    ],
}