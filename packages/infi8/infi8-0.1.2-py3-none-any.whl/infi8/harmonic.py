def harmonic_series(n):
    """Generates the first n terms of a harmonic series."""
    return [1 / i for i in range(1, n + 1)]

def harmonic_nth_term(n):
    """Finds the nth term of a harmonic series."""
    return 1 / n

def harmonic_sum(n):
    """Finds the sum of the first n terms of a harmonic series."""
    return sum(1 / i for i in range(1, n + 1))
