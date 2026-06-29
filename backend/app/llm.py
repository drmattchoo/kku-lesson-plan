from __future__ import annotations

import json
import re

from openai import OpenAI

from app.config import settings

_JSON_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _strip_code_fence(text: str) -> str:
    return _JSON_FENCE.sub("", text.strip())


class LLMProvider:
    """Thin wrapper around the KKU gateway (gen.ai.kku.ac.th) — one OpenAI-compatible
    endpoint that routes to either backend (Claude or GPT) by model name."""

    def __init__(self, model: str | None = None):
        self.client = OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)
        self.model = model or settings.active_model

    def complete(self, system: str, user: str, *, max_tokens: int = 1024) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    def complete_json(self, system: str, user: str, *, max_tokens: int = 2048) -> dict:
        raw = self.complete(system, user, max_tokens=max_tokens)
        return json.loads(_strip_code_fence(raw))


def get_provider(model: str | None = None) -> LLMProvider:
    return LLMProvider(model=model)
