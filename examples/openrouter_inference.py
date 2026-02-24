#!/usr/bin/env python3
"""Example: call OpenRouter with an OA ephemeral key."""

from __future__ import annotations

import argparse

import oa


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True, help="Ephemeral OA key")
    parser.add_argument("--model", default="openai/gpt-5.2-chat")
    parser.add_argument("--prompt", required=True)
    args = parser.parse_args()

    response = oa.chat_completion(
        key=args.key,
        model=args.model,
        prompt=args.prompt,
        destination="openrouter",
    )
    print(response.get("output_text") or "")


if __name__ == "__main__":
    main()
