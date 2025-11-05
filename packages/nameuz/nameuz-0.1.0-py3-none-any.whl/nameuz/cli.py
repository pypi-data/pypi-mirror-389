import json
import argparse
from nameuz.meaning import Meaning


def main():
    parser = argparse.ArgumentParser(description="Search Uzbek name meanings from ismlar.com")
    parser.add_argument("--search", "-s", type=str, help="Name to search meaning for")
    parser.add_argument("--page", "-p", type=int, default=1, help="Page number (default: 1)")

    args = parser.parse_args()

    if args.search:
        m = Meaning(args.search, args.page)
        result = m.response()

        if result:
            print(json.dumps(result, indent=4, ensure_ascii=False))
        else:
            print("No results found.")
    else:
        parser.print_help()