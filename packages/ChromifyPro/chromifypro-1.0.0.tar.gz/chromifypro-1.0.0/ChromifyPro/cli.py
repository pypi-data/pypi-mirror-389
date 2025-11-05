import argparse
from .utils import load_from_zip

def main():
    parser = argparse.ArgumentParser(description="Chromify CLI – color manipulation and conversion")
    parser.add_argument("--load-zip", type=str, help="Load color templates from a ZIP file")
    parser.add_argument("--list", action="store_true", help="List loaded colors")

    args = parser.parse_args()

    if args.load_zip:
        colors = load_from_zip(args.load_zip)
        print(f"Loaded {len(colors)} colors from {args.load_zip}")
        if args.list:
            for c in colors:
                print(f"- {c.to_hex()}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()