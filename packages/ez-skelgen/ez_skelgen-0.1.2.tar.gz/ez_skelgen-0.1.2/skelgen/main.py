import os
import argparse
from .parser import parse_tree_structure, parse_indent_structure
from .builder import build_structure

def main():
    parser = argparse.ArgumentParser(description="Generate a C project skeleton with template code.")
    parser.add_argument("input", help="Path to the structure file (.txt).")
    parser.add_argument("-o", "--output", default="output", help="Output directory")
    parser.add_argument("-a", "--author", default="Unknown", help="Author name for templates")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if any(('├' in l or '└' in l or '│' in l) for l in lines):
        structure = parse_tree_structure(lines)
    else:
        structure = parse_indent_structure(lines)

    os.makedirs(args.output, exist_ok=True)
    build_structure(structure, args.output, author=args.author)
    print(f"C skeleton generated successfully in: {args.output}")

if __name__ == "__main__":
    main()
