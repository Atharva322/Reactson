"""Command line entry points for Reactson."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from reactson import __version__
from reactson.api.app import health_payload
from reactson.core.phases import PHASES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reactson", description="Reactson agent runtime")
    subcommands = parser.add_subparsers(dest="command")

    subcommands.add_parser("health", help="Print Reactson health status")
    subcommands.add_parser("version", help="Print Reactson version")
    subcommands.add_parser("phases", help="List Reactson implementation phases")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "health":
        print(json.dumps(health_payload(), sort_keys=True))
        return 0

    if args.command == "version":
        print(__version__)
        return 0

    if args.command == "phases":
        for phase in PHASES:
            print(f"{phase.index}: {phase.name} [{phase.status}]")
        return 0

    parser.print_help()
    return 0


def health_main() -> int:
    return main(["health"])


if __name__ == "__main__":
    raise SystemExit(main())
