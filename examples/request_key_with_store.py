#!/usr/bin/env python3
"""Example: load tickets from file and request an ephemeral key."""

from __future__ import annotations

import argparse
import json

import oa


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ticket_file")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--name", default="OA-SDK-Example")
    args = parser.parse_args()

    lease = oa.request_unlinkable_key(
        ticket_file=args.ticket_file,
        ticket_count=args.count,
        key_name=args.name,
    )

    print(
        json.dumps(
            {
                "key": lease["key"],
                "station_id": lease["station_id"],
                "expires_at": lease["expires_at"],
                "tickets_consumed": lease["tickets_consumed"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
