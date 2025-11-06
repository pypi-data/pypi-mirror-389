from .funfacts import fun_fact
from .smalltalk import smallTalk
from .banter import banter
from .pickuplines import pickUpLine
from .compliments import compliment

import argparse

def main() -> None:
    parser = argparse.ArgumentParser(prog="chatterpy_mistral")

    # funfacts
    parser.add_argument("--fact", action="store_true", help="print a fun fact")
    parser.add_argument("--category", default="general",
                        help="fun fact category (general, science, history, animals)")
    parser.add_argument("--rarity", default="common",
                        help="fun fact rarity (common, rare)")

    # smalltalk
    parser.add_argument("--smalltalk", action="store_true",
                        help="print a small talk line")
    parser.add_argument("--question", action="store_true",
                        help="when used with --smalltalk, ask a question; otherwise print a comment")
    parser.add_argument("--comment", action="store_true",
                        help="alias: if set, smalltalk will prefer comments")

    # common options
    parser.add_argument("--kind", choices=["classic", "poetic", "funny", "nerdy"],
                        help="style/kind for pickup lines (and other funcs if applicable)")
    parser.add_argument("--name", default="", help="optional name")

    # banter
    parser.add_argument("--intensity", choices=["mild", "medium", "intense"],
                        help="tone intensity for banter/compliment")
    parser.add_argument("--banter", action="store_true", help="print a playful banter/insult")

    # pickup lines
    parser.add_argument("--pickup", action="store_true", help="print a pickup line")

    # compliments
    parser.add_argument("--compliment", action="store_true", help="print a compliment")

    args = parser.parse_args()

    # funfacts
    if args.fact:
        print(fun_fact(category=args.category, rarity=args.rarity))

    # smalltalk
    if args.smalltalk:
        prefer_question = True if args.question else False
        if args.comment:
            prefer_question = False
        print(smallTalk(prefer_question))

    # banter
    if args.banter:
        intensity = args.intensity if args.intensity else "medium"
        name = args.name if args.name else ""
        print(banter(intensity, name))

    # pickup
    if args.pickup:
        kind = args.kind if args.kind else "classic"
        print(pickUpLine(kind, args.name))

    # compliment
    if args.compliment:
        _map = {"mild": 1, "medium": 2, "intense": 3}
        inten = _map.get(args.intensity or "medium", 2)
        print(compliment(name=args.name, intensity=inten))

if __name__ == "__main__":
    main()
