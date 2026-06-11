"""
Input generators for the fuzzer.

Two generation strategies are provided:
  - random:   samples uniformly across the valid input range
  - boundary: concentrates samples near a known "interesting" value
              (the offset/length identified manually in Exercise 4)

Both strategies return plain integers - target_4a.run_4a() interprets
this as an offset, target_4b.run_4b() interprets this as a payload
length.
"""

import random

# --- Exercise 4 findings: update these to match your results ---
OFFSET_4A_RANGE = (0, 128)
OFFSET_4A_BOUNDARY = 24      # offset that triggers steal_password()

LENGTH_4B_RANGE = (0, 500)
LENGTH_4B_BOUNDARY = 264     # input length that triggers the segfault


def random_value(low, high):
    """Uniformly sample an integer in [low, high] (inclusive)."""
    return random.randint(low, high)


def boundary_value(low, high, center, spread):
    """
    Sample an integer concentrated near `center`.

    Uses a normal distribution with mean=center and the given
    standard deviation, then rounds to the nearest integer and
    clamps the result into [low, high].
    """
    value = int(round(random.gauss(center, spread)))
    return max(low, min(high, value))


# --- 4A generators ---

def random_offset_4a():
    """Random strategy: any offset in the valid 0-128 range."""
    return random_value(*OFFSET_4A_RANGE)


def boundary_offset_4a(spread=5):
    """Boundary strategy: offsets clustered around the offset-24 finding."""
    return boundary_value(*OFFSET_4A_RANGE, center=OFFSET_4A_BOUNDARY, spread=spread)


# --- 4B generators ---

def random_length_4b():
    """Random strategy: any payload length in the valid 0-500 range."""
    return random_value(*LENGTH_4B_RANGE)


def boundary_length_4b(spread=15):
    """Boundary strategy: lengths clustered around the segfault threshold."""
    return boundary_value(*LENGTH_4B_RANGE, center=LENGTH_4B_BOUNDARY, spread=spread)


if __name__ == "__main__":
    # Quick sanity check: print a sample of values from each generator
    print("4A random:  ", [random_offset_4a() for _ in range(10)])
    print("4A boundary:", [boundary_offset_4a() for _ in range(10)])
    print("4B random:  ", [random_length_4b() for _ in range(10)])
    print("4B boundary:", [boundary_length_4b() for _ in range(10)])
