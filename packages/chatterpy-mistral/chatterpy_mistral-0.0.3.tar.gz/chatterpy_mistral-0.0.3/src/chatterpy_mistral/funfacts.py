import random

#data
FACTS = {
    "general": {
        "common": [
            "Bananas are berries, but strawberries aren’t.",
            "Octopuses have three hearts.",
        ],
        "rare": [
            "Sharks existed before trees.",
            "Honey never spoils—it can last for millennia.",
        ],
    },
    "science": {
        "common": [
            "A day on Venus is longer than a year on Venus.",
            "Humans share about 60% of their DNA with bananas.",
        ],
        "rare": [
            "Water can boil and freeze at the same time (triple point).",
            "There are more stars in the universe than grains of sand on Earth.",
        ],
    },
    "history": {
        "common": [
            "Oxford University predates the Aztec Empire.",
            "Cleopatra lived closer to us than to the building of the pyramids.",
        ],
        "rare": [
            "Ancient Roman concrete can 'self-heal'.",
            "The first computer bug was a real moth (1947).",
        ],
    },
    "animals": {
        "common": [
            "A group of flamingos is called a flamboyance.",
            "Cows can have best friends.",
        ],
        "rare": [
            "Axolotls can regenerate parts of their brain.",
            "Some jellyfish can revert to a juvenile state.",
        ],
    },
}


def fun_fact(category: str = "general", rarity: str = "common") -> str:
    """
    Return one fun fact.
    Falls back to general and common if inputs are unknown.
    """
    cat = FACTS.get(category) or FACTS["general"]
    pool = cat.get(rarity) or cat["common"]
    return random.choice(pool)
