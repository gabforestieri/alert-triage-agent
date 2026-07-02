"""Lightweight LLM client abstraction to support multiple model providers.

This module provides a small wrapper API that normalizes responses into
an object with a `content` attribute: a list of blocks with `type` and
`text` attributes. That matches the shape the rest of the code expects
from the Anthropic client and lets us plug in OpenAI (and others) easily.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, List

import anthropic
import openai


@dataclass
class _Block:
    type: str
    text: str


class _NormalizedResponse:
    def __init__(self, blocks: List[_Block]):
        self.content = blocks


class LLMFactory:
    @staticmethod
    def get_client(provider: str = "anthropic", api_key: str | None = None, **kwargs) -> Any:
        provider = (provider or "anthropic").lower()
        if provider in ("anthropic", "claude"):
            return _AnthropicClient(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        if provider in ("openai", "gpt"):
            return _OpenAIClient(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        raise ValueError(f"Unknown provider: {provider}")


class _AnthropicClient:
    def __init__(self, api_key: str | None = None):
        # Keep direct access to anthropic.Anthropic so tests can patch it
        self._client = anthropic.Anthropic(api_key=api_key)

    @property
    def messages(self):
        return self._client.messages


class _OpenAIClient:
    def __init__(self, api_key: str | None = None):
        if api_key:
            openai.api_key = api_key

    class messages:
        @staticmethod
        def create(model: str, max_tokens: int | None = None, system: str | None = None, messages: list | None = None):
            # forward to openai.ChatCompletion.create and normalize
            resp = openai.ChatCompletion.create(model=model, messages=messages, max_tokens=max_tokens)
            # build blocks from choices
            blocks = []
            for choice in resp.get("choices", []):
                msg = choice.get("message", {})
                text = msg.get("content") or choice.get("text") or ""
                blocks.append(_Block(type="text", text=text))
            return _NormalizedResponse(blocks)
