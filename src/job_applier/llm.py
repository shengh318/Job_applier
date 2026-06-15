# src/job_applier/llm.py
"""LLM provider abstraction for Ollama, OpenAI, and Anthropic."""
from __future__ import annotations

import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

PROVIDERS = ("ollama", "openai", "anthropic")


class LLMProvider:
    """Unified interface for calling LLM APIs."""

    def __init__(self, provider: str, model: str, api_url: str = "", api_key: str = ""):
        self.provider = provider
        self.model = model
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self._http = httpx.AsyncClient(timeout=120.0)

    def _get_endpoint(self) -> str:
        if self.provider == "ollama":
            return f"{self.api_url}/api/generate"
        elif self.provider == "openai":
            return "https://api.openai.com/v1/chat/completions"
        elif self.provider == "anthropic":
            return "https://api.anthropic.com/v1/messages"
        raise ValueError(f"Unknown provider: {self.provider}")

    def _get_headers(self) -> dict[str, str]:
        if self.provider == "openai":
            return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        elif self.provider == "anthropic":
            return {"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
        return {"Content-Type": "application/json"}

    def _build_payload(self, prompt: str) -> dict[str, Any]:
        if self.provider == "ollama":
            return {"model": self.model, "prompt": prompt, "stream": False, "format": "json"}
        elif self.provider == "openai":
            return {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
            }
        elif self.provider == "anthropic":
            return {
                "model": self.model,
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}],
            }
        raise ValueError(f"Unknown provider: {self.provider}")

    def _extract_response(self, data: dict[str, Any]) -> str:
        if self.provider == "ollama":
            return data.get("response", "")
        elif self.provider == "openai":
            return data["choices"][0]["message"]["content"]
        elif self.provider == "anthropic":
            return data["content"][0]["text"]
        raise ValueError(f"Unknown provider: {self.provider}")

    async def generate(self, prompt: str, retries: int = 2) -> dict[str, Any]:
        """Send prompt to LLM and return parsed JSON response."""
        endpoint = self._get_endpoint()
        headers = self._get_headers()
        payload = self._build_payload(prompt)

        last_error = None
        for attempt in range(retries + 1):
            try:
                resp = await self._http.post(endpoint, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                raw_text = self._extract_response(data)
                return json.loads(raw_text)
            except (json.JSONDecodeError, KeyError, httpx.HTTPStatusError) as e:
                last_error = e
                logger.warning("LLM attempt %d failed: %s", attempt + 1, e)
                continue

        raise RuntimeError(f"LLM failed after {retries + 1} attempts: {last_error}")

    async def close(self):
        await self._http.aclose()


def create_llm_provider(provider: str, model: str, api_url: str = "", api_key: str = "") -> LLMProvider:
    """Factory function to create an LLM provider."""
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown LLM provider: {provider}. Must be one of: {PROVIDERS}")
    return LLMProvider(provider=provider, model=model, api_url=api_url, api_key=api_key)
