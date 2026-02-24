#!/usr/bin/env python3
"""
Request API key using inference tickets.

This script implements the `request_key` workflow from oa-chat, allowing you
to redeem Privacy Pass tickets for ephemeral API keys.

Usage:
    python request_key.py                               # show available model tiers
    python request_key.py tickets.json                  # request key with 1 ticket
    python request_key.py tickets.json --tier 3x       # request key with 3 tickets
    python request_key.py tickets.json --json          # output as JSON

Ticket file format (exported from oa-chat):
    {
        "data": {
            "tickets": {
                "active": [{"finalized_ticket": "...", ...}, ...]
            }
        }
    }

Requirements: pip install requests
"""

import argparse
import json
import sys
from pathlib import Path

import requests

# Open Anonymity org server base URL
ORG_API_BASE = "https://org.openanonymity.ai"


# =============================================================================
# Core Functions (can be imported and used elsewhere)
# =============================================================================

def fetch_tiers():
    """
    Fetch model-to-ticket-cost mapping from the org server.

    Returns:
        dict: {model_id: ticket_cost} e.g. {"anthropic/claude-3-haiku": 1, ...}
              Empty dict on error.
    """
    try:
        r = requests.get(f"{ORG_API_BASE}/chat/model-tickets", timeout=10)
        return r.json() if r.ok else {}
    except:
        return {}


def load_tickets(path):
    """
    Load active (unused) tickets from an exported JSON file.

    Handles multiple export formats from oa-chat:
    - Full export: {data: {tickets: {active: [...]}}}
    - Tickets-only: {data: {active: [...]}}
    - Raw array: [...]

    Args:
        path: Path to the ticket JSON file

    Returns:
        list: Active ticket objects, each containing 'finalized_ticket' key
    """
    data = json.loads(Path(path).read_text())


    # Navigate nested structure to find the tickets array
    if isinstance(data, dict):
        if "data" in data:
            data = data["data"]
        if "tickets" in data:
            data = data["tickets"]
        if "active" in data:
            data = data["active"]

    tickets = data if isinstance(data, list) else []

    # Filter out consumed/archived tickets
    return [
        t for t in tickets
        if t.get("finalized_ticket")
        and not t.get("consumed_at")
        and t.get("status", "").lower() not in ("archived", "consumed", "used")
    ]


def request_key(tickets, count=1, name="OA-Script-Key"):
    """
    Request an API key by redeeming inference tickets.

    Args:
        tickets: List of ticket objects (from load_tickets)
        count: Number of tickets to redeem (determines model tier access)
        name: Identifier for the key (for logging/tracking)

    Returns:
        dict with keys: key, tickets_consumed, expires_at, station_id

    Raises:
        ValueError: Not enough tickets
        RuntimeError: API request failed
    """
    if len(tickets) < count:
        raise ValueError(f"Need {count} tickets, have {len(tickets)}")

    # Build the authorization header with ticket token(s)
    tokens = ",".join(t["finalized_ticket"] for t in tickets[:count])
    auth = f"InferenceTicket token{'s' if count > 1 else ''}={tokens}"

    # POST to the org server's request_key endpoint
    r = requests.post(
        f"{ORG_API_BASE}/api/request_key",
        headers={"Content-Type": "application/json", "Authorization": auth},
        json={"name": name},
        timeout=30,
    )

    data = r.json()
    if not r.ok:
        raise RuntimeError(data.get("detail") or data.get("error") or f"Failed ({r.status_code})")

    return {
        "key": data["key"],
        "tickets_consumed": data.get("tickets_consumed", count),
        "expires_at": data.get("expires_at"),
        "station_id": data["station_id"],
    }


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Request API key using inference tickets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Run without arguments to see available model tiers.",
    )
    parser.add_argument("ticket_file", nargs="?", help="Ticket JSON file (exported from oa-chat)")
    parser.add_argument("--tier", default="1x", help="Tickets to use: 1x, 2x, 3x, etc. (default: 1x)")
    parser.add_argument("--name", default="OA-Script-Key", help="Key name for identification")
    parser.add_argument("--tiers", action="store_true", help="Show available model tiers")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    args = parser.parse_args()

    # Show available tiers (default when no ticket file provided)
    if args.tiers or not args.ticket_file:
        tiers = fetch_tiers()
        if not tiers:
            print("Could not fetch tiers from server")
            return
        # Group models by ticket cost
        by_cost = {}
        for model, cost in tiers.items():
            by_cost.setdefault(cost, []).append(model)
        for cost in sorted(by_cost):
            print(f"\n{cost}x ({cost} ticket{'s' if cost > 1 else ''}):")
            for m in sorted(by_cost[cost]):
                print(f"  {m}")
        return

    # Request a key
    try:
        tickets = load_tickets(args.ticket_file)
        count = int(args.tier.lower().replace("x", ""))
        result = request_key(tickets, count, args.name)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Key: {result['key']}")
            print(f"Tickets used: {result['tickets_consumed']}")
            print(f"Expires: {result['expires_at']}")
            print(f"Remaining: {len(tickets) - count}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
