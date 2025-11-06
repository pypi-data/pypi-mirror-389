def geometric_series(a, n, r):
    """Generates the first n terms of a geometric series."""
    return [a * (r ** i) for i in range(n)]

def geometric_nth_term(a, n, r):
    """Finds the nth term of a geometric series."""
    return a * (r ** (n - 1))

def geometric_sum(a, n, r):
    """Finds the sum of the first n terms of a geometric series."""
    if r == 1:
        return a * n
    return a * (1 - r**n) / (1 - r)

def geometric_infinite_sum(a, r):
    """Finds the sum of an infinite geometric series (only if |r| < 1)."""
    if abs(r) >= 1:
        raise ValueError("Infinite geometric series sum only converges if |r| < 1")
    return a / (1 - r)
