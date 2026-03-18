"""CLI for fixmystreet."""
import sys, json, argparse
from .core import Fixmystreet

def main():
    parser = argparse.ArgumentParser(description="FixMyStreet — AI Infrastructure Reporter. Report potholes, broken lights, and infrastructure issues with AI classification.")
    parser.add_argument("command", nargs="?", default="status", choices=["status", "run", "info"])
    parser.add_argument("--input", "-i", default="")
    args = parser.parse_args()
    instance = Fixmystreet()
    if args.command == "status":
        print(json.dumps(instance.get_stats(), indent=2))
    elif args.command == "run":
        print(json.dumps(instance.process(input=args.input or "test"), indent=2, default=str))
    elif args.command == "info":
        print(f"fixmystreet v0.1.0 — FixMyStreet — AI Infrastructure Reporter. Report potholes, broken lights, and infrastructure issues with AI classification.")

if __name__ == "__main__":
    main()
