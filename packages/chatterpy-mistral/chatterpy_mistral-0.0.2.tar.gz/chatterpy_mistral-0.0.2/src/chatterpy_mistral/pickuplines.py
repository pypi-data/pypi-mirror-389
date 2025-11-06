import random

PICKUPLINES = {
    "classic": [
        "you have a great smile.",
        "you make the room feel brighter.",
        "your kindness stands out.",
        "you have awesome energy.",
    ],
    "poetic": [
        "your presence feels like morning sunshine.",
        "your laugh sounds like a good song.",
        "you carry a little bit of starlight with you.",
        "you’re a calm breeze on a warm day.",
    ],
    "funny": [
        "you’re the human version of the ‘skip intro’ button, instantly great.",
        "your vibe is like perfect wifi, I feel a connection.",
        "you’re meme-worthy in the best way.",
        "you’re plot-armor for bad moods.",
    ],
    "nerdy": [
        "you’re a clean solution in a messy codebase.",
        "your curiosity has amazing test coverage.",
        "you’re big-O of awesome: constant impact.",
        "you’re a well-documented feature of the universe.",
    ],
}

def pickUpLine(kind, name=""):
    """
    Returns a compliment
    kind is required, name is optional
    """
    if kind not in PICKUPLINES:
        raise ValueError("unknown kind (use classic, poetic, funny, nerdy)")

    line = random.choice(PICKUPLINES[kind])

    if name:
        return f"{name}, {line}"
    return line
