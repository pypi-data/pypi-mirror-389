import argparse
from emojiguessr import make_quiz_item, check_answer, score
from emojiguessr.data import _EMOJI_BANK


def run_quiz(num_questions, theme, case_sensitive, allow_partial, max_attempts, input_fn = input, output_fn = print):
    s = 0
    for i in range(1, num_questions + 1):
        item = make_quiz_item(theme=theme)
        clue = item["clue"]
        answer = item["answer"]

        output_fn(f"\nQuestion {i}/{num_questions}")
        output_fn(f"Theme: {item['theme']}")
        output_fn(f"Emoji: {clue}")

        attempts_left = max_attempts
        while attempts_left > 0:
            guess = input_fn("Your guess: ")

            is_right = check_answer(
                correct=answer,
                guess=guess,
                case_sensitive=case_sensitive,
                allow_partial=allow_partial,
            )

            s = score(s, correct=is_right)

            if is_right:
                output_fn("✅ Correct!")
                break
            else:
                attempts_left -= 1
                if attempts_left > 0:
                    output_fn(f"❌ Wrong! {attempts_left} attempts left.")
                else:
                    output_fn(f"❌ Nope — it was: {answer}")

    output_fn(f"\nFinal score: {s}/{num_questions}")


def list_themes(output_fn = print):
    output_fn("Available themes:")
    for theme in sorted(_EMOJI_BANK.keys()):
        output_fn(f"  - {theme}")


def list_commands(output_fn = print):
    output_fn("Available commands:")
    output_fn("  --num-questions, -n    : Number of questions to ask (default: 3)")
    output_fn("  --theme, -t            : Emoji theme to use (default: food)")
    output_fn("  --case-sensitive       : Make answers case-sensitive (default: off)")
    output_fn("  --no-partial           : Disable partial matches")
    output_fn(
        "  --max-attempts, -a     : Maximum number of attempts per question (default: 1)"
    )
    output_fn("  --list-themes, -lt     : List available themes and exit")
    output_fn("  --list-commands, -lc   : List available commands and exit")


def main():
    parser = argparse.ArgumentParser(
        prog="emojiguessr",
        description="Play a quick emoji guessing game in your terminal.",
    )
    parser.add_argument(
        "--num-questions",
        "-n",
        type=int,
        default=3,
        help="Number of questions to ask (default: 3)",
    )
    parser.add_argument(
        "--theme",
        "-t",
        default="food",
        help="Emoji theme to use (default: food). Use --list-themes to see options.",
    )
    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Make answers case-sensitive (default: off)",
    )
    parser.add_argument(
        "--no-partial",
        action="store_true",
        help="Disable partial matches (so 'jurassic' won't match 'jurassic park')",
    )
    parser.add_argument(
        "--max-attempts",
        "-a",
        type=int,
        default=1,
        help="Maximum number of attempts per question (default: 1)",
    )
    parser.add_argument(
        "--list-themes",
        "-lt",
        action="store_true",
        help="List available themes and exit.",
    )
    parser.add_argument(
        "--list-commands",
        "-lc",
        action="store_true",
        help="List available commands and exit.",
    )

    args = parser.parse_args()

    if args.list_themes:
        list_themes()
        return

    if args.list_commands:
        list_commands()
        return

    run_quiz(
        num_questions=args.num_questions,
        theme=args.theme,
        case_sensitive=args.case_sensitive,
        allow_partial=not args.no_partial,
        max_attempts=args.max_attempts,
    )


if __name__ == "__main__":
    main()
