"""Entry point for the AI Customer Support Email Agent."""

import argparse
import logging
import sys

from src.agent import EmailAgent
from src.config import Config


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=level,
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AI Customer Support Email Agent",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=["once", "continuous"],
        default="once",
        help="'once' processes available emails and exits; "
             "'continuous' polls at the configured interval.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.verbose)

    config = Config()
    try:
        config.validate()
    except ValueError as exc:
        logging.error("Configuration error: %s", exc)
        logging.error("Copy .env.example to .env and fill in the required values.")
        return 1

    agent = EmailAgent(config=config)

    if args.mode == "continuous":
        agent.run_continuous()
    else:
        summary = agent.run_once()
        print(
            f"Run complete: fetched={summary.emails_fetched} "
            f"processed={summary.emails_processed} "
            f"failed={summary.emails_failed}"
        )
        for result in summary.results:
            status = "✓" if result.response_sent else "✗"
            print(f"  [{status}] uid={result.uid} category={result.category} to={result.sender}")
            if result.error:
                print(f"      Error: {result.error}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
