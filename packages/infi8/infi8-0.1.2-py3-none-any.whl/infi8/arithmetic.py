def arithmetic_series(a, n, d):
    """Generates the first n terms of an arithmetic series."""
    return [a + i * d for i in range(n)]

def arithmetic_nth_term(a, n, d):
    """Finds the nth term of an arithmetic series."""
    return a + (n - 1) * d

def arithmetic_sum(a, n, d):
    """Finds the sum of the first n terms of an arithmetic series."""
    return (n / 2) * (2 * a + (n - 1) * d)
