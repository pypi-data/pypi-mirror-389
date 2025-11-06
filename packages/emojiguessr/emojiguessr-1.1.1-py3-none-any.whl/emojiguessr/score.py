def score(current_score, correct=True, points=1):
    if correct:
        return current_score + points
    return current_score
