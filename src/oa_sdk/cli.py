from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .client import OAClient
from .simple import (
    DEFAULT_KEY_NAME,
    DEFAULT_TICKET_FILE,
    archive_tickets,
    add_tickets,
    chat_completion,
    list_stations,
    request_confidential_key,
    request_unlinkable_key,
    show_tickets,
)


def _print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oa-sdk",
        description="Open Anonymity SDK CLI (simple surface)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    tiers = subparsers.add_parser(
        "model-tiers",
        aliases=["tiers"],
        help="Fetch model -> ticket cost map",
    )
    tiers.set_defaults(handler=handle_model_tiers)

    stations = subparsers.add_parser(
        "list-stations",
        aliases=["stations"],
        help="Fetch online OA stations from oa-org",
    )
    stations.add_argument("--version", type=int, choices=[1, 2], default=2, help="Station API version")
    stations.set_defaults(handler=handle_list_stations)

    unlinkable = subparsers.add_parser(
        "request-unlinkable-key",
        aliases=["key-request"],
        help="Redeem tickets for a standard OA unlinkable key",
    )
    unlinkable.add_argument("ticket_file", nargs="?", default=DEFAULT_TICKET_FILE)
    unlinkable.add_argument("--count", type=int, default=1, help="Tickets to consume")
    unlinkable.add_argument("--name", default=DEFAULT_KEY_NAME, help="Key name")
    unlinkable.add_argument("--no-save", action="store_true", help="Do not persist ticket file changes")
    unlinkable.set_defaults(handler=handle_request_unlinkable_key)

    confidential = subparsers.add_parser(
        "request-confidential-key",
        help="Redeem tickets for OA confidential key flow via oa-org station relay",
    )
    confidential.add_argument("ticket_file", nargs="?", default=DEFAULT_TICKET_FILE)
    confidential.add_argument("--count", type=int, default=1, help="Tickets to consume")
    confidential.add_argument("--name", default=DEFAULT_KEY_NAME, help="Key name")
    confidential.add_argument(
        "--require-attestation",
        action="store_true",
        help="Fail unless station/org signatures are present in response",
    )
    confidential.add_argument("--no-save", action="store_true", help="Do not persist ticket file changes")
    confidential.set_defaults(handler=handle_request_confidential_key)

    completion = subparsers.add_parser(
        "chat-completion",
        aliases=["infer"],
        help="Run one chat completion call using an existing key",
    )
    completion.add_argument("--key", "--token", dest="key", required=True, help="OA key / provider key")
    completion.add_argument("--model", required=True, help="Target model id")
    completion.add_argument("--prompt", required=True, help="Prompt text")
    completion.add_argument(
        "--destination",
        "--backend",
        dest="destination",
        choices=[
            "openrouter",
            "gemini-provider-direct",
            "openai-provider-direct",
            "provider-direct",
            "tee-gateway",
        ],
        default="openrouter",
        help="Inference destination",
    )
    completion.add_argument("--base-url", default=None, help="Base URL override (required for some destinations)")
    completion.add_argument("--temperature", type=float, default=None)
    completion.add_argument("--max-output-tokens", type=int, default=None)
    completion.set_defaults(handler=handle_chat_completion)

    add = subparsers.add_parser(
        "add-tickets",
        aliases=["ticket-redeem"],
        help="Redeem a ticket code and append resulting tickets to local store",
    )
    add.add_argument("credential", help="Ticket code / credential")
    add.add_argument("ticket_file", nargs="?", default=DEFAULT_TICKET_FILE)
    add.add_argument(
        "--count",
        "--requested-count",
        dest="requested_count",
        type=int,
        default=None,
        help="Override inferred ticket count",
    )
    add.add_argument(
        "--ticket-file",
        dest="ticket_file_option",
        default=None,
        help=argparse.SUPPRESS,
    )
    add.add_argument("--no-save", action="store_true", help="Do not persist ticket file changes")
    add.set_defaults(handler=handle_add_tickets)

    show = subparsers.add_parser(
        "show-tickets",
        aliases=["tickets"],
        help="Display ticket counts and sample entries",
    )
    show.add_argument("ticket_file", nargs="?", default=DEFAULT_TICKET_FILE)
    show.add_argument("--include-tokens", action="store_true", help="Include finalized ticket tokens in output")
    show.add_argument("--limit", type=int, default=5, help="Max active/archived entries to show")
    show.set_defaults(handler=handle_show_tickets)

    archive = subparsers.add_parser(
        "archive-tickets",
        help="Move active tickets to archived state",
    )
    archive.add_argument("ticket_file", nargs="?", default=DEFAULT_TICKET_FILE)
    archive.add_argument("--count", type=int, default=1)
    archive.add_argument("--order", choices=["head", "tail"], default="head")
    archive.add_argument("--status", default="archived")
    archive.add_argument("--no-save", action="store_true", help="Do not persist ticket file changes")
    archive.set_defaults(handler=handle_archive_tickets)

    return parser


def handle_model_tiers(args: argparse.Namespace) -> int:
    with OAClient() as client:
        payload = client.keys.fetch_model_tickets()
    _print_json(payload)
    return 0


def handle_list_stations(args: argparse.Namespace) -> int:
    payload = list_stations(version=args.version)
    _print_json(payload)
    return 0


def handle_request_unlinkable_key(args: argparse.Namespace) -> int:
    payload = request_unlinkable_key(
        ticket_file=args.ticket_file,
        ticket_count=args.count,
        key_name=args.name,
        save=not args.no_save,
    )
    _print_json(payload)
    return 0


def handle_request_confidential_key(args: argparse.Namespace) -> int:
    payload = request_confidential_key(
        ticket_file=args.ticket_file,
        ticket_count=args.count,
        key_name=args.name,
        require_attestation=args.require_attestation,
        save=not args.no_save,
    )
    _print_json(payload)
    return 0


def handle_chat_completion(args: argparse.Namespace) -> int:
    payload = chat_completion(
        key=args.key,
        model=args.model,
        prompt=args.prompt,
        destination=args.destination,
        base_url=args.base_url,
        temperature=args.temperature,
        max_output_tokens=args.max_output_tokens,
    )
    _print_json(payload)
    return 0


def handle_add_tickets(args: argparse.Namespace) -> int:
    ticket_file = args.ticket_file_option or args.ticket_file
    payload = add_tickets(
        credential=args.credential,
        ticket_file=ticket_file,
        requested_count=args.requested_count,
        save=not args.no_save,
    )
    _print_json(payload)
    return 0


def handle_show_tickets(args: argparse.Namespace) -> int:
    payload = show_tickets(
        ticket_file=args.ticket_file,
        include_tokens=args.include_tokens,
        limit=args.limit,
    )
    _print_json(payload)
    return 0


def handle_archive_tickets(args: argparse.Namespace) -> int:
    payload = archive_tickets(
        ticket_file=args.ticket_file,
        count=args.count,
        order=args.order,
        status=args.status,
        save=not args.no_save,
    )
    _print_json(payload)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return int(args.handler(args))
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
