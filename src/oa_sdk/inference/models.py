from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Sequence


@dataclass(frozen=True)
class ResponseInputMessage:
    role: str
    content: str


@dataclass(frozen=True)
class ResponseRequest:
    model: str
    input: str | Sequence[ResponseInputMessage] | Sequence[Mapping[str, str]]
    stream: bool = False
    temperature: float | None = None
    max_output_tokens: int | None = None
    extra: Mapping[str, Any] = field(default_factory=dict)

    def as_messages(self) -> List[Dict[str, str]]:
        if isinstance(self.input, str):
            return [{"role": "user", "content": self.input}]

        messages: List[Dict[str, str]] = []
        for item in self.input:
            if isinstance(item, ResponseInputMessage):
                messages.append({"role": item.role, "content": item.content})
            else:
                role = item.get("role")
                content = item.get("content")
                if isinstance(role, str) and isinstance(content, str):
                    messages.append({"role": role, "content": content})
        return messages


@dataclass(frozen=True)
class AccessCredential:
    token: str
    header_name: str = "Authorization"
    prefix: str = "Bearer "

    def apply(self, headers: Dict[str, str]) -> Dict[str, str]:
        headers[self.header_name] = f"{self.prefix}{self.token}" if self.prefix else self.token
        return headers
