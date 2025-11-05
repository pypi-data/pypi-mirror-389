"""Cli interface for Moodsmith"""

import argparse

from . import __version__
from .core import funny, motivational, negative, positive
from .locales import (FUNNY_TEMPLATE, MOTIVATIONAL_TEMPLATES,
                      NEGATIVE_MOTIVATIONAL, POSITIVE_TEMPLATES)


def create_parser():
    """Parse command-line arguments"""

    lang_keys = set(POSITIVE_TEMPLATES.keys())
    lang_keys.update(FUNNY_TEMPLATE.keys())
    lang_keys.update(MOTIVATIONAL_TEMPLATES.keys())
    lang_keys.update(NEGATIVE_MOTIVATIONAL.keys())
    languages = sorted(list(lang_keys))
    categories = ["positive", "funny", "motivational", "negative"]
    intensities = ["soft", "medium", "hard"]

    parser = argparse.ArgumentParser(
        description="""Motivational sentences for programmers.""",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "-c",
        "--category",
        choices=categories,
        default="motivational",
        help="""Category of the message.
  positive: A positive quote.
  funny: A funny sentence.
  motivational: An earnest motivational message.
  negative: A negatively-toned motivational message.
  (default: motivational)""",
    )

    parser.add_argument(
        "-l",
        "--language",
        choices=languages,
        default="en",
        help=f"""Message language.
  Available: {', '.join(languages)}
  Falls back to 'en' if a language is unsupported
  for a given category.
  (default: en)""",
    )

    parser.add_argument(
        "-i",
        "--intensity",
        choices=intensities,
        default="medium",
        help=f"""Tone intensity.
  Available: {', '.join(intensities)}
  Applies to 'motivational' and 'negative' categories.
  (default: medium)""",
    )

    parser.add_argument(
        "-e",
        "--enthusiasm",
        type=int,
        choices=range(0, 6),
        default=2,
        metavar="{0-5}",
        help="""Controls punctuation (enthusiasm).
  0: ends with a period (.)
  1-5: ends with that many exclamation points (!)
  Applies to 'positive', 'funny', and 'negative' categories.
  (default: 2)""",
    )

    parser.add_argument(
        "-n", "--name", type=str, help="Name to address in the message."
    )

    parser.add_argument(
        "-v", "--version", action="version", version=f"moodsmith {__version__}"
    )

    return parser


def main():
    """Main driver function called through CLI"""

    parser = create_parser()
    args = parser.parse_args()
    message = ""
    try:
        if args.category == "positive":
            message = positive(
                language=args.language,
                name=args.name,
                enthusiasm=args.enthusiasm
            )
        elif args.category == "funny":
            message = funny(
                language=args.language,
                name=args.name,
                enthusiasm=args.enthusiasm
            )
        elif args.category == "motivational":
            message = motivational(
                language=args.language,
                intensity=args.intensity,
                name=args.name
            )
        elif args.category == "negative":
            message = negative(
                language=args.language,
                name=args.name,
                enthusiasm=args.enthusiasm,
                intensity=args.intensity
            )

        print(message)

    except Exception as e:
        print(f"An error occurred: {e}")
        parser.print_help()


if __name__ == "__main__":
    main()
