import math
from collections import Counter

def existential_uncertainty(text: str) -> float:
    """
    Compute a Shannon-style entropy score for a text string,
    interpreted as a proxy for existential uncertainty.
    """
    if not text:
        return 0.0

    freq = Counter(text.lower())
    total = sum(freq.values())
    probs = [count / total for count in freq.values()]

    entropy = -sum(p * math.log(p, 2) for p in probs)
    normalized = entropy / math.log(len(freq), 2)
    return round(normalized, 4)
