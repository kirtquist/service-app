"""Minimal CLI demo — prints catalog + optionally calls OpenRouter."""

import argparse
import json


def main() -> None:
    from service_app.catalog import PRICE_DATABASE
    from service_app.ingestion import parse_service_call

    parser = argparse.ArgumentParser(description="Service App MVP demo")
    parser.add_argument(
        "--parse",
        metavar="TRANSCRIPT",
        help="Send a technician log line to OpenRouter and print parsed JSON.",
    )
    args = parser.parse_args()

    if args.parse:
        try:
            result = parse_service_call(args.parse)
        except ValueError as exc:
            print(f"Parse error: {exc}", file=__import__("sys").stderr)
            raise SystemExit(1) from exc
        print(json.dumps(result.model_dump(), indent=2))
        return

    print("Catalog (sample electrician-style parts; swap for plumbers):")
    for name, price in PRICE_DATABASE.items():
        print(f"  {name}: ${price:.2f}")
    print()
    print("Set OPENROUTER_API_KEY and pass --parse \"...\" to test LLM ingestion.")


if __name__ == "__main__":
    main()
