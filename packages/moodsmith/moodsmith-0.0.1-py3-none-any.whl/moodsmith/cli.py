'''Command Line Interface for Moodsmith'''

import argparse
from typing import Callable

from . import __version__
from .core import motivational, positive


def main():
    '''Main driver function for CLI'''

    parser = argparse.ArgumentParser(
        prog="moodsmith",
        description=(
            "A package designed to motivate you while you work,"
            " directly in your terminal."
        ),
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "-l", "--language",
        choices=["en", "es", "fr"],  # Based on locales.py
        default="en",
        help="Language of the message (default: en).",
    )
    subparsers = parser.add_subparsers(
        dest="category",
        required=True,
        title="Categories",
        help="The type of message to generate.",
    )
    pos_parser = subparsers.add_parser(
        "positive",
        help="Get a positive, uplifting quote.",
        description="Get a positive, uplifting quote.",
    )
    pos_parser.add_argument(
        "-e", "--enthusiasm",
        type=int,
        choices=range(0, 6),
        default=2,
        metavar="[0-5]",
        help="Set enthusiasm level, 0=period, 5=!!!!! (default: 2).",
    )
    pos_parser.add_argument(
        "-n", "--name",
        help="Person to address.",
    )
    pos_parser.set_defaults(func=positive)
    mot_parser = subparsers.add_parser(
        "motivational",
        help="Get a short motivational message.",
        description="Get a short motivational message.",
    )
    mot_parser.add_argument(
        "-i", "--intensity",
        choices=["soft", "medium", "hard"],
        default="medium",
        help="Intensity/tone of the message (default: medium).",
    )
    mot_parser.add_argument(
        "-n", "--name",
        help="Person to address.",
    )
    mot_parser.set_defaults(func=motivational)
    subparsers.add_parser(
        "funny",
        help="Get a funny joke (not yet implemented).",
    )
    subparsers.add_parser(
        "negative",
        help="Get a negative-motivational quote (not yet implemented).",
    )
    args = parser.parse_args()
    if hasattr(args, "func"):
        kwargs = vars(args)
        func_to_call: Callable = kwargs.pop("func")
        kwargs.pop("category", None)
        try:
            message = func_to_call(**kwargs)
            print(message)
        except TypeError as e:
            print(f"Error calling function: {e}")
            print("This category may not be fully implemented yet.")

    else:
        print(f"The '{args.category}' category is not yet implemented.")


if __name__ == "__main__":
    main()
