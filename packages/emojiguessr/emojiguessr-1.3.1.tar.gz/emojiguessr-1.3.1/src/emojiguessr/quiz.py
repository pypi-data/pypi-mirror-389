from .data import get_theme_item


def make_quiz_item(theme="food"):
    emoji, answer = get_theme_item(theme)
    return {"clue": emoji, "answer": answer, "theme": theme}


def _normalize(text):
    return text.strip().lower()


def check_answer(correct, guess, case_sensitive=False, allow_partial=True):
    if case_sensitive:
        if allow_partial:
            return correct.startswith(guess)
        return correct == guess

    correct_n = _normalize(correct)
    guess_n = _normalize(guess)

    if allow_partial:
        return correct_n.startswith(guess_n)
    return correct_n == guess_n
