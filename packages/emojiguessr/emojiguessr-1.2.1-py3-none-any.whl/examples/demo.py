"""
Demo showcasing all features of the emojiguessr package.
Run this file to see examples of all available functions.
"""

from emojiguessr import random_emojis, make_quiz_item, check_answer, score


def pause():
    input("\nPress Enter to continue to the next demo...")


def demo_random_emojis():
    print("=" * 60)
    print("DEMO: random_emojis() - Get random emoji clues")
    print("=" * 60)

    # Get 3 random food emojis (default)
    print("\n1. Get 3 random food emojis (default):")
    food_emojis = random_emojis()
    print(f"   {' '.join(food_emojis)}")

    # Get 5 random animal emojis
    print("\n2. Get 5 random animal emojis:")
    animal_emojis = random_emojis(count=5, theme="animals")
    print(f"   {' '.join(animal_emojis)}")

    # Get 2 random movie emojis
    print("\n3. Get 2 random movie emojis:")
    movie_emojis = random_emojis(count=2, theme="movies")
    print(f"   {' '.join(movie_emojis)}")

    # Get random emojis from different themes
    print("\n4. Try different themes:")
    themes = ["games", "cities", "feelings", "dev"]
    for theme in themes:
        emojis = random_emojis(count=2, theme=theme)
        print(f"   {theme.capitalize()}: {' '.join(emojis)}")


def demo_make_quiz_item():
    print("\n" + "=" * 60)
    print("DEMO: make_quiz_item() - Create quiz questions")
    print("=" * 60)

    # Create a food quiz item (default)
    print("\n1. Create a food quiz item (default):")
    food_item = make_quiz_item()
    print(f"   Clue: {food_item['clue']}")
    print(f"   Answer: {food_item['answer']}")
    print(f"   Theme: {food_item['theme']}")

    # Create quiz items from different themes
    print("\n2. Create quiz items from different themes:")
    themes = ["animals", "movies", "games", "cities"]
    for theme in themes:
        item = make_quiz_item(theme=theme)
        print(f"   {theme.capitalize()}: {item['clue']} → {item['answer']}")


def demo_check_answer():
    print("\n" + "=" * 60)
    print("DEMO: check_answer() - Validate user answers")
    print("=" * 60)

    correct_answer = "lord of the rings"

    # Default behavior: case-insensitive, partial match allowed
    print("\n1. Default (case-insensitive, partial match):")
    test_cases = ["lord", "Lord", "LORD OF THE RINGS", "lord of the rings"]
    for guess in test_cases:
        result = check_answer(correct_answer, guess)
        status = "✅" if result else "❌"
        print(f"   {status} '{guess}' → {result}")

    # Case-sensitive mode
    print("\n2. Case-sensitive mode:")
    test_cases = ["lord", "Lord", "lord of the rings"]
    for guess in test_cases:
        result = check_answer(correct_answer, guess, case_sensitive=True)
        status = "✅" if result else "❌"
        print(f"   {status} '{guess}' → {result}")

    # Exact match only (no partial)
    print("\n3. Exact match only (no partial):")
    test_cases = ["lord", "lord of the rings", "Lord of the Rings"]
    for guess in test_cases:
        result = check_answer(correct_answer, guess, allow_partial=False)
        status = "✅" if result else "❌"
        print(f"   {status} '{guess}' → {result}")

    # Case-sensitive AND exact match
    print("\n4. Case-sensitive AND exact match:")
    test_cases = ["lord of the rings", "Lord of the Rings", "lord"]
    for guess in test_cases:
        result = check_answer(
            correct_answer, guess, case_sensitive=True, allow_partial=False
        )
        status = "✅" if result else "❌"
        print(f"   {status} '{guess}' → {result}")


def demo_score():
    print("\n" + "=" * 60)
    print("DEMO: score() - Track quiz scores")
    print("=" * 60)

    # Basic scoring
    print("\n1. Basic scoring (1 point per correct answer):")
    current = 0
    print(f"   Starting score: {current}")

    current = score(current, correct=True)
    print(f"   After correct answer: {current}")

    current = score(current, correct=False)
    print(f"   After wrong answer: {current}")

    current = score(current, correct=True)
    print(f"   After another correct: {current}")

    # Custom points
    print("\n2. Custom points per answer:")
    current = 0
    print(f"   Starting score: {current}")

    current = score(current, correct=True, points=5)
    print(f"   After correct (5 points): {current}")

    current = score(current, correct=True, points=10)
    print(f"   After correct (10 points): {current}")

    current = score(current, correct=False, points=3)
    print(f"   After wrong (3 points): {current}")


def demo_simple_quiz():
    print("\n" + "=" * 60)
    print("DEMO: Simple Quiz Workflow")
    print("=" * 60)

    print("\nLet's simulate a 3-question quiz:\n")

    current_score = 0
    questions = 3

    for i in range(1, questions + 1):
        # Create a quiz item
        item = make_quiz_item(theme="food")

        print(f"Question {i}/{questions}")
        print(f"Emoji: {item['clue']}")

        # Simulate user guesses
        if i == 1:
            guess = item["answer"]  # Correct
            print(f"User guesses: '{guess}'")
        elif i == 2:
            guess = item["answer"][:3]  # Partial match
            print(f"User guesses: '{guess}' (partial)")
        else:
            guess = "wrong answer"  # Wrong
            print(f"User guesses: '{guess}'")

        # Check answer
        is_correct = check_answer(item["answer"], guess)

        # Update score
        current_score = score(current_score, correct=is_correct)

        if is_correct:
            print("✅ Correct!")
        else:
            print(f"❌ Wrong! The answer was: {item['answer']}")

        print(f"Current score: {current_score}/{i}\n")

    print(f"Final score: {current_score}/{questions}")


def main():
    print("\nThis demo will showcase all features of the emojiguessr package.")
    print("Press Enter after each section to continue.\n")
    pause()

    demo_random_emojis()
    pause()

    demo_make_quiz_item()
    pause()

    demo_check_answer()
    pause()

    demo_score()
    pause()

    demo_simple_quiz()

    print("\n" + "=" * 60)
    print("Demo complete! Try the CLI with: pipenv run emojiguessr")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
