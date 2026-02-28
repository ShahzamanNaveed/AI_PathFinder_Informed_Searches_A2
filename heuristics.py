import math


def manhattan(a, b):
    """
    Manhattan distance between two grid cells.
    a, b: tuples of (row, col)
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def euclidean(a, b):
    """
    Euclidean distance between two grid cells.
    a, b: tuples of (row, col)
    """
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)