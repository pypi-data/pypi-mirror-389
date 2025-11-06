def symmetry_index(sequence):
    """
    Computes how symmetric a numerical sequence is.
    Perfectly symmetric → 1.0
    """
    n = len(sequence)
    if n == 0:
        return 0.0

    mirrored = sequence[::-1]
    matches = sum(1 for a, b in zip(sequence, mirrored) if a == b)
    return round(matches / n, 3)
