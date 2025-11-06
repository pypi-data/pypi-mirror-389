from difflib import SequenceMatcher

def resonance_score(word1: str, word2: str) -> float:
    """
    Compute a rough semantic resonance between two words.
    Placeholder: uses character-level similarity.
    """
    return round(SequenceMatcher(None, word1, word2).ratio(), 3)
