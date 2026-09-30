import argparse
import json

from .app import serve
from .config import Study, data_root
from .corpus import collect
from .demo import seed_demo
from .store import Store


def main():
    parser = argparse.ArgumentParser(description="Reviewed palette analysis for Nature, Science, and Cell")
    parser.add_argument("--data-dir", default=None)
    sub = parser.add_subparsers(dest="command", required=True)
    web = sub.add_parser("serve", help="Open the local review and analysis application")
    web.add_argument("--port", type=int, default=8765)
    web.add_argument("--demo", action="store_true", help="Create separately labeled synthetic examples")
    fetch = sub.add_parser("collect", help="Collect a limited OA pilot using Europe PMC and PMC S3")
    fetch.add_argument("--start-year", type=int, default=2021)
    fetch.add_argument("--end-year", type=int, default=2025)
    fetch.add_argument("--limit", type=int, default=5, help="Maximum metadata records scanned per journal, not guaranteed eligible papers")
    fetch.add_argument("--journals", nargs="+", choices=["Nature", "Science", "Cell"], default=["Nature", "Science", "Cell"])
    fetch.add_argument("--pmcids", nargs="+", help="Optional explicit PMC identifiers, still checked against journal/date/OA scope")
    fetch.add_argument("--include-manuscripts", action="store_true", help="Also retrieve licensed accepted manuscripts; excluded from final-version rankings by default")
    sub.add_parser("demo", help="Generate synthetic examples in a separate dataset")
    args = parser.parse_args()
    store = Store(data_root(args.data_dir))
    if args.command == "serve":
        if args.demo:
            seed_demo(store)
        serve(store, args.port)
    elif args.command == "demo":
        seed_demo(store)
        print("Synthetic examples generated; the real corpus is unchanged.")
    else:
        report = collect(store, Study(start_year=args.start_year, end_year=args.end_year, journals=tuple(args.journals)), args.limit,
                         lambda message: print(message, flush=True), pmcids=args.pmcids, include_manuscripts=args.include_manuscripts)
        print(json.dumps(report, indent=2))
        if report["errors"]:
            raise SystemExit(2)


if __name__ == "__main__":
    main()
