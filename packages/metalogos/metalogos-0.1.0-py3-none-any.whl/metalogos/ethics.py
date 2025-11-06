def moral_dilemma(outcomes, philosophy="utilitarian"):
    """
    Evaluate moral trade-offs between outcomes.
    Each outcome is a dict: {"utility": x, "harm": y}.
    """
    if philosophy == "utilitarian":
        scored = [(o["utility"] - o["harm"], o) for o in outcomes]
    elif philosophy == "stoic":
        scored = [(-abs(o["harm"]), o) for o in outcomes]
    elif philosophy == "existential":
        scored = [(o["utility"] * 0.5 - o["harm"] * 0.5, o) for o in outcomes]
    else:
        raise ValueError("Unknown philosophy")

    best = max(scored, key=lambda x: x[0])[1]
    return best
