import re
import os

ALLOC_PATTERN = re.compile(r'\b(malloc|calloc|realloc|new(\[\])?)\b')
FREE_PATTERN = re.compile(r'\b(free|delete(\[\])?)\b')

def analyze_source(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(filepath, 'r') as f:
        code = f.readlines()

    allocs = 0
    frees = 0
    alloc_lines = []
    free_lines = []

    for i, line in enumerate(code, 1):
        if ALLOC_PATTERN.search(line):
            allocs += 1
            alloc_lines.append(i)
        if FREE_PATTERN.search(line):
            frees += 1
            free_lines.append(i)

    return {
        "allocs": allocs,
        "frees": frees,
        "unfreed_allocations": allocs - frees,
        "lines": {
            "alloc": alloc_lines,
            "free": free_lines
        }
    }
