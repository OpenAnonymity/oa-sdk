#!/usr/bin/env python3
"""Example: end-to-end flow (tickets -> key -> inference)."""

from __future__ import annotations

import argparse
import json

import oa


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ticket_file")
    parser.add_argument("--model", default="openai/gpt-5.2-chat")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--ticket-count", type=int, default=None)
    args = parser.parse_args()

    lease = oa.request_unlinkable_key(
        ticket_file=args.ticket_file,
        ticket_count=args.ticket_count or 1,
    )
    response = oa.chat_completion(
        key=lease["key"],
        model=args.model,
        prompt=args.prompt,
        destination="openrouter",
    )

    print(
        json.dumps(
            {
                "response_id": response["response_id"],
                "output_text": response["output_text"],
                "tickets_consumed": lease["tickets_consumed"],
                "station_id": lease["station_id"],
                "expires_at": lease["expires_at"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
