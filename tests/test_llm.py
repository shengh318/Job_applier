# tests/test_llm.py
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from job_applier.llm import LLMProvider, create_llm_provider


def test_create_ollama_provider():
    provider = create_llm_provider("ollama", "llama3", api_url="http://localhost:11434")
    assert isinstance(provider, LLMProvider)
    assert provider.provider == "ollama"
    assert provider.model == "llama3"


def test_create_openai_provider():
    provider = create_llm_provider("openai", "gpt-4o-mini", api_key="sk-test")
    assert isinstance(provider, LLMProvider)
    assert provider.provider == "openai"
    assert provider.model == "gpt-4o-mini"


def test_create_anthropic_provider():
    provider = create_llm_provider("anthropic", "claude-3-5-sonnet", api_key="sk-ant-test")
    assert isinstance(provider, LLMProvider)
    assert provider.provider == "anthropic"


def test_create_unknown_provider():
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        create_llm_provider("unknown", "model")


@pytest.mark.asyncio
async def test_generate_returns_json():
    provider = create_llm_provider("ollama", "llama3", api_url="http://localhost:11434")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "response": json.dumps({"fields": [], "click": None, "status": "done"})
    }

    with patch.object(provider._http, "post", new_callable=AsyncMock, return_value=mock_response):
        result = await provider.generate("test prompt")
        assert result["status"] == "done"


@pytest.mark.asyncio
async def test_generate_retries_on_invalid_json():
    provider = create_llm_provider("ollama", "llama3", api_url="http://localhost:11434")
    bad_response = MagicMock()
    bad_response.status_code = 200
    bad_response.json.return_value = {"response": "not json at all"}

    good_response = MagicMock()
    good_response.status_code = 200
    good_response.json.return_value = {
        "response": json.dumps({"fields": [], "click": None, "status": "done"})
    }

    with patch.object(provider._http, "post", new_callable=AsyncMock, side_effect=[bad_response, good_response]):
        result = await provider.generate("test prompt")
        assert result["status"] == "done"
