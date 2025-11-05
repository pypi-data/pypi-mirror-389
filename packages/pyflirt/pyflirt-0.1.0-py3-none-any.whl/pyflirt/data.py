# pyflirt/data.py
BANK = {
    "nerdy": [
        {"text": "Are you made of copper and tellurium? Because you’re Cu-Te.", "cheese": 2},
        {"text": "Are you a quantum tunnel? Because you went straight through my barriers.", "cheese": 3},
        {"text": "Is your name Wi-Fi? Because I feel a strong connection.", "cheese": 3},
        {"text": "Are you a neural net, {name}? Because I keep overfitting to you.", "cheese": 4},
    ],
    "poetic": [
        {"text": "{name}, shall I compare thee to a stable release? Thou art rarer and far more dependable.", "cheese": 4},
        {"text": "I’d cross the version gulf for thee, and tag a release upon thy smile.", "cheese": 3},
    ],
    "cs": [
        {"text": "If love were a bug, I’d still refuse to close your ticket.", "cheese": 1},
        {"text": "Do you believe in love at first compile, {name}, or should I re-run?", "cheese": 2},
        {"text": "You must be Git—my heart commits to you.", "cheese": 2},
    ],
    "math": [
        {"text": "You must be my limit—I’m approaching you from every direction.", "cheese": 4},
        {"text": "If we were vectors, we’d be perfectly aligned.", "cheese": 2},
        {"text": "Are you √-1? You’re unreal—and I can’t stop imagining us.", "cheese": 4},
        {"text": "We are coprime; the only common divisor is one heart.", "cheese": 3},
    ],
    "classic": [
        {"text": "Are you a magician? Because whenever I look at you, everyone else disappears.", "cheese": 2},
    ],
}

COMPLIMENT_TEMPLATES = {
    "developer": {
        "sweet": [
            "Your code is cleaner than a freshly cloned repo{name_bit}",
            "You commit kindness with every push{name_bit}",
            "You’re the pull request everyone approves instantly{name_bit}",
        ],
        "cheeky": [
            "You refactor hearts, not just code{name_bit}",
            "You’ve got more charm than a recursive function{name_bit}",
            "You must be a keyboard shortcut—because you’re my type{name_bit}",
        ],
        "nerdy": [
            "You debug my sadness faster than VSCode{name_bit}",
            "You’re the semicolon that completes my statement{name_bit}",
            "If beauty were an algorithm, you’d be O(1){name_bit}",
        ],
    },
    "designer": {
        "sweet": [
            "Your aesthetic sense brightens every UI{name_bit}",
            "You bring color theory to my grayscale days{name_bit}",
            "Pixels align themselves just to please you{name_bit}",
        ],
        "cheeky": [
            "You must be a vector—because you’ve got direction{name_bit}",
            "Are you a grid system? Because my heart is well-aligned{name_bit}",
            "You kerningly complete me{name_bit}",
        ],
        "nerdy": [
            "You optimize whitespace like a legend{name_bit}",
            "Your Figma files are pure poetry{name_bit}",
            "Even Helvetica blushes when you walk in{name_bit}",
        ],
    },
    "manager": {
        "sweet": [
            "You lead with empathy{name_bit}",
            "Your standups make Mondays bearable{name_bit}",
            "You’re the reason meetings actually end early{name_bit}",
        ],
        "cheeky": [
            "You manage hearts better than timelines{name_bit}",
            "You’re my favorite deliverable{name_bit}",
            "You’ve got more charisma than a sprint demo{name_bit}",
        ],
        "nerdy": [
            "You allocate my attention like a well-balanced backlog{name_bit}",
            "KPIs envy your energy{name_bit}",
            "Your OKRs? Outrageously Kind & Radiant{name_bit}",
        ],
    },
    "data": {
        "sweet": [
            "You turn noise into beauty{name_bit}",
            "Every dataset wishes it were as clean as your heart{name_bit}",
            "You make outliers feel included{name_bit}",
        ],
        "cheeky": [
            "You must be a correlation—because you complete my regression{name_bit}",
            "You’re my favorite variable{name_bit}",
            "You pivot-table my emotions{name_bit}",
        ],
        "nerdy": [
            "Your confidence interval? 100%{name_bit}",
            "You’re statistically significant in my life{name_bit}",
            "Your curves fit any model{name_bit}",
        ],
    },
}

def categories():
    """Return a sorted list of all available pickup line categories."""
    return sorted(BANK.keys())
