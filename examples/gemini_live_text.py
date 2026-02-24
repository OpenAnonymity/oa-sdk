#!/usr/bin/env python3
"""Example: Gemini Live API ephemeral token + one text turn."""

from __future__ import annotations

import argparse
import asyncio
import json

from oa_sdk.client import OAClient


async def run(args: argparse.Namespace) -> None:
    with OAClient() as client:
        live = client.inference.gemini_live_client(api_key=args.api_key)
        token = live.create_ephemeral_token(
            uses=1,
            expire_seconds=1800,
            new_session_expire_seconds=60,
            live_model=args.model,
        )

        response = await live.generate_text(
            token_name=token.name,
            model=args.model,
            prompt=args.prompt,
        )

    print(
        json.dumps(
            {
                "token_name": token.name,
                "output_text": response.output_text,
            },
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True, help="Long-lived Gemini API key")
    parser.add_argument("--model", required=True, help="Gemini live model id")
    parser.add_argument("--prompt", required=True, help="Prompt text")
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
