from e2e_models import EmptyElement


def levenshtein_distance(a: list[str], b: list[str]):
    """
    Computes the Levenshtein distance between two sequences and returns:
      - distance (int)
      - matrix (2D list of ints)
    """
    m = len(a)
    n = len(b)

    # matrix of (m+1) x (n+1)
    d = [[0] * (n + 1) for _ in range(m + 1)]

    # Prefill deletions
    for i in range(m + 1):
        d[i][0] = i

    # Prefill insertions
    for j in range(n + 1):
        d[0][j] = j

    # Fill DP matrix
    for j in range(1, n + 1):
        for i in range(1, m + 1):
            substitution_cost = 0 if a[i - 1] == b[j - 1] else 1

            d[i][j] = min(
                d[i - 1][j] + 1,  # deletion
                d[i][j - 1] + 1,  # insertion
                d[i - 1][j - 1] + substitution_cost,  # substitution
            )

    return d[m][n], d


def backtrack_alignment(a, b, d):
    """
    Walks backward through the Levenshtein matrix and reconstructs
    the best alignment between sequences `a` and `b`.
    """
    i = len(a)
    j = len(b)

    aligned_a = []
    aligned_b = []

    while i > 0 or j > 0:

        # Case 1: We must insert all remaining b (gaps in a)
        if i == 0:
            aligned_a.insert(0, EmptyElement())
            aligned_b.insert(0, b[j - 1])
            j -= 1

        # Case 2: We must delete all remaining a (gaps in b)
        elif j == 0:
            aligned_a.insert(0, a[i - 1])
            aligned_b.insert(0, EmptyElement())
            i -= 1

        # Case 3: Match
        elif d[i][j] == d[i - 1][j - 1] and a[i - 1].neume == b[j - 1].neume:
            aligned_a.insert(0, a[i - 1])
            aligned_b.insert(0, b[j - 1])
            i -= 1
            j -= 1

        # Case 4: Substitution
        elif d[i][j] == d[i - 1][j - 1] + 1:
            aligned_a.insert(0, a[i - 1])
            aligned_b.insert(0, b[j - 1])
            i -= 1
            j -= 1

        # Case 5: Deletion
        elif d[i][j] == d[i - 1][j] + 1:
            aligned_a.insert(0, a[i - 1])
            aligned_b.insert(0, EmptyElement())
            i -= 1

        # Case 6: Insertion
        elif d[i][j] == d[i][j - 1] + 1:
            aligned_a.insert(0, EmptyElement())
            aligned_b.insert(0, b[j - 1])
            j -= 1

        else:
            # Should not happen, but we guard for debugging
            raise RuntimeError(f"Invalid backtrack step at i={i}, j={j}")

    return aligned_a, aligned_b
