import random

# separate banter into 3 categories, "mild", "medium," and "intense"
insults = {
    "mild": [
        f"if I gave you a penny for your thoughts, I'd get change back.",
        f"the closest you'll come to a brainstorm is a light drizzle.",
        f"you're like a software update: nobody asked for you.",
        f"your secret is safe with me, because I wasn't listening.",
        f"you have the personality of a loading screen.",
    ],
    "medium": [
        f"I envy everyone who hasn't met you.",
        f"you'll go far someday. And I hope you stay there.",
        f"you look like something I drew with my left hand.",
        f"if ignorance is bliss, you must be ecstatic at all times.",
        f"you're the human equivalent of a participation trophy.",
        f"you bring joy to every room you exit.",


    ],
    "intense": [
        f"you're like a cloud: when you disappear, it's a beautiful day.",
        f"you're not stupid, you just have bad luck thinking.",
        f"you're the kind of person who would get lost in their own thoughts and never be found.",
        f"somewhere out there is a tree working hard to replace the oxygen you waste.",
        f"you're like a Monday morning: nobody's happy to see you.",
        f"you look like a 'before' picture.",
    ],
}

def banter(intensity, name=""):
    """
    Returns a playful insult.
    intensity is required (use mild, medium, or intense), name is optional.
    """
    result = random.choice(insults[intensity])
    
    if name:
        return f"{name}, {result}"
    return result