# Small Talk function
# Implement function that returns small talk.

import random 

questions = [
    "How's your day going?",
    "What's your favorite color?", 
    "What's your favorite programming language?",
    "I’m running purely on caffeine today — you?",
    "Do you usually listen to music when you work?",
    "What’s your go-to comfort show or movie?",
    "I’ve been meaning to start reading/watching something new — any recommendations?",
    "What do you like to do outside of school/work?",
    "Do you have any hobbies you’ve picked up recently?", 
    "What kind of music are you into?",
    "Are you more of an introvert or extrovert?",
    "If you could travel anywhere right now, where would you go?", 
    "What’s a random skill you wish you had?",
    "What’s your comfort food?",
    "Do you like podcasts or audiobooks?",
    "Are you a cat person, dog person, or both?",
    "Anything fun or random happen to you today?"
]

comments = [
    "The weather is nice today.",
    "I’m convinced every day this week has been Tuesday.",
    "I need a nap.", 
    "It’s one of those days where coffee feels more like a necessity than a choice.", 
    "My brain clocked out hours ago.",
    "People who can wake up early and be nice about it scare me a little.",
    "Socks with sandals are just misunderstood geniuses.",
    "Avocado toast is overrated, but I’d still eat it.",
    "Pineapple on pizza is disgusting.",
    "I hate vegetables.", 
    "Movies are boring.", 
    "'The Office' isn't funny."
]


def smallTalk(question): 
    if question: 
        return random.choice(questions)
    return random.choice(comments)


