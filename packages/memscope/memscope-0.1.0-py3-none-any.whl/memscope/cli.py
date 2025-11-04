import sys
from .core import analyze_source

def main():
    if len(sys.argv) != 2:
        print("Usage: python -m memscope <path-to-c-file>")
        sys.exit(1)

    filepath = sys.argv[1]
    result = analyze_source(filepath)
    print("Memory Analysis:")
    print(result)
