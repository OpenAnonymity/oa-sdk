# Minimal SDK Example

This is the shortest practical `import oa` flow:
1. request an OA unlinkable key from local tickets
2. call one chat completion with that key

## Prerequisites

- Ticket file present at `oa-chat-tickets.json` (or pass a custom path).
- Install SDK in editable mode:

```bash
pip install -e .
```

## Python (minimal)

```python
import oa

key = oa.request_unlinkable_key(
    ticket_file="oa-chat-tickets.json",
    ticket_count=1,
)

response = oa.chat_completion(
    key=key["key"],
    model="openai/gpt-5.2-chat",
    prompt="ping",
    destination="openrouter",
)

print(response["output_text"])
```

## CLI (minimal)

```bash
oa-sdk request-unlinkable-key oa-chat-tickets.json --count 1
oa-sdk chat-completion --key <OA_KEY> --model openai/gpt-5.2-chat --prompt "ping" --destination openrouter
```

## Ticket management quick commands

```bash
oa-sdk add-tickets <ticket_code> oa-chat-tickets.json
oa-sdk show-tickets oa-chat-tickets.json --limit 5
```
