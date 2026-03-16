from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Mapping, Sequence

from ..errors import OAProtocolError


@dataclass(frozen=True)
class OpenRouterModel:
    id: str
    name: str
    created: int | None = None
    canonical_slug: str | None = None
    context_length: int | None = None
    description: str | None = None
    pricing: dict[str, str] = field(default_factory=dict)

    @property
    def is_free_text_model(self) -> bool:
        prompt = _decimal_or_none(self.pricing.get("prompt"))
        completion = _decimal_or_none(self.pricing.get("completion"))
        request = _decimal_or_none(self.pricing.get("request", "0"))

        zero = Decimal("0")
        return prompt == zero and completion == zero and request == zero


def parse_openrouter_model_catalog(data: object) -> list[OpenRouterModel]:
    if not isinstance(data, Mapping):
        raise OAProtocolError("OpenRouter model catalog response is not an object")

    models_raw = data.get("data")
    if not isinstance(models_raw, list):
        raise OAProtocolError("OpenRouter model catalog response missing data list")

    models: list[OpenRouterModel] = []
    for item in models_raw:
        if not isinstance(item, Mapping):
            continue

        model_id = item.get("id")
        name = item.get("name")
        if not isinstance(model_id, str) or not isinstance(name, str):
            continue

        pricing_raw = item.get("pricing")
        pricing = (
            {
                key: value
                for key, value in pricing_raw.items()
                if isinstance(key, str) and isinstance(value, str)
            }
            if isinstance(pricing_raw, Mapping)
            else {}
        )

        models.append(
            OpenRouterModel(
                id=model_id,
                name=name,
                created=_int_or_none(item.get("created")),
                canonical_slug=_str_or_none(item.get("canonical_slug")),
                context_length=_int_or_none(item.get("context_length")),
                description=_str_or_none(item.get("description")),
                pricing=pricing,
            )
        )

    return models


def select_latest_openrouter_model(models: Sequence[OpenRouterModel]) -> OpenRouterModel:
    if not models:
        raise OAProtocolError("No OpenRouter models available for selection")
    return max(
        models,
        key=lambda model: (model.created is not None, model.created or -1, model.id),
    )


def _decimal_or_none(value: str | None) -> Decimal | None:
    if value is None:
        return None

    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def _int_or_none(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _str_or_none(value: object) -> str | None:
    return value if isinstance(value, str) else None
