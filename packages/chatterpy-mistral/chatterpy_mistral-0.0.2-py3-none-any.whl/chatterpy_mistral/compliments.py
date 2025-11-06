import random
from typing import Optional, Literal

Intensity = Literal[1, 2, 3]
Style = Literal["classic", "geeky", "poetic"]
Category = Literal["personality", "appearance", "accomplishment", "specific"]

def compliment(
    name: str = "",
    intensity: Intensity = 1,
    style: Style = "classic",
    category: Category = "personality",
    detail: Optional[str] = None,
) -> str:
    intensity = 1 if intensity < 1 else 3 if intensity > 3 else intensity

    base = {
        "personality": {
            1: [
                "You're such a thoughtful person.",
                "You have a gift for making others feel valued.",
                "I appreciate your honesty.",
            ],
            2: [
                "Your confidence is inspiring.",
                "Your kindness is contagious.",
                "You have an amazing sense of humor.",
            ],
            3: [
                "Your presence lifts everyone around you.",
                "Your integrity and empathy set the standard.",
                "Your strength under pressure is remarkable.",
            ],
        },
        "appearance": {
            1: [
                "I love your sense of style.",
                "That color looks great on you.",
                "You look great today.",
            ],
            2: [
                "Your outfit is on point.",
                "You always add something unique to your look.",
                "Your smile lights up the room.",
            ],
            3: [
                "Your look today is stunning.",
                "Your style is effortlessly impressive.",
                "You have a standout, polished presence.",
            ],
        },
        "accomplishment": {
            1: [
                "I admire your creativity.",
                "You're a considerate, dependable team player.",
                "You have a real way with words.",
            ],
            2: [
                "You're an exceptional problem-solver.",
                "Your ideas are fresh and insightful.",
                "You structure complex tasks brilliantly.",
            ],
            3: [
                "Your work sets a new bar for quality.",
                "Your leadership on tough tasks is outstanding.",
                "You consistently turn hard problems into clear wins.",
            ],
        },
        "specific": {
            1: [
                "I was really impressed by {detail}.",
                "Your thoughtful approach to {detail} stood out.",
            ],
            2: [
                "The way you handled {detail} showed real skill.",
                "{detail} was a smart, well-judged choice.",
            ],
            3: [
                "{detail} was exceptional—truly impressive.",
                "Your execution on {detail} was outstanding.",
            ],
        },
    }

    pool = base.get(category, base["personality"])[intensity]
    sentence = random.choice(pool)

    if category == "specific":
        sentence = sentence.replace("{detail}", detail or "that")

    style_tail = {
        "classic": "",
        "geeky": " It's elegantly optimized.",
        "poetic": " Like sunlight through calm water.",
    }[style]

    if name:
        sentence = f"{name}, {sentence}"

    banned = ["for someone like you", "than you look", "actually pretty good", "not bad", "surprisingly good"]
    if any(b in sentence.lower() for b in banned):
        sentence = f"{name+', ' if name else ''}You're doing great."

    return (sentence + style_tail).strip()
#TODO
