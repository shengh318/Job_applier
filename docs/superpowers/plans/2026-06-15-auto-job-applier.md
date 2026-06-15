# Auto Job Applier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python tool that searches Indeed, fills job applications automatically using AI, handles external ATS redirects, creates accounts, and notifies the user.

**Architecture:** Python app talks to Camoufox browser via REST API. An AI-first Application Engine reads page accessibility snapshots and fills forms. A Config system, Account Manager, and Notification System support the core flow.

**Tech Stack:** Python 3.11+, Camoufox REST API, httpx, PyYAML, PyPDF2, sqlite3, plyer (desktop notifications)

---

## File Structure

```
job_applier/
├── pyproject.toml
├── config.yaml                 # Main config
├── profile.yaml                # User profile
├── src/
│   └── job_applier/
│       ├── __init__.py
│       ├── __main__.py         # CLI entry point
│       ├── config.py           # Config loading & validation
│       ├── browser.py          # Camoufox REST API client
│       ├── llm.py              # LLM provider abstraction (Ollama/OpenAI/Anthropic)
│       ├── prompt.py           # Prompt building & response parsing
│       ├── search.py           # Indeed job search engine
│       ├── application.py      # Application engine (AI-first form filler)
│       ├── accounts.py         # Account manager (SQLite)
│       ├── notifications.py    # Desktop notifications
│       └── runner.py           # Main orchestrator
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_browser.py
│   ├── test_llm.py
│   ├── test_prompt.py
│   ├── test_search.py
│   ├── test_application.py
│   ├── test_accounts.py
│   └── test_notifications.py
└── docs/
    └── superpowers/
        ├── specs/
        └── plans/
```

---

### Task 1: Project Setup & Config

**Files:**
- Create: `pyproject.toml`
- Create: `src/job_applier/__init__.py`
- Create: `src/job_applier/config.py`
- Create: `tests/__init__.py`
- Create: `tests/test_config.py`
- Create: `config.yaml` (example)
- Create: `profile.yaml` (example)

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "job-applier"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "httpx>=0.27",
    "pyyaml>=6.0",
    "PyPDF2>=3.0",
    "plyer>=2.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Create src/job_applier/__init__.py**

```python
"""Auto Job Applier - AI-powered job application tool."""
```

- [ ] **Step 3: Write the failing test for config loading**

```python
# tests/test_config.py
import os
import tempfile
import pytest
from job_applier.config import load_config, Config


def test_load_config_from_yaml(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
llm:
  provider: ollama
  model: llama3
  api_url: http://localhost:11434
  api_key: ""
search:
  title: "Software Engineer"
  location: "San Francisco"
  remote_only: true
profile:
  file: ./profile.yaml
  resume: ./resume.pdf
notifications:
  desktop: true
  log_file: ./logs/applications.jsonl
""")
    config = load_config(str(config_file))
    assert isinstance(config, Config)
    assert config.llm.provider == "ollama"
    assert config.llm.model == "llama3"
    assert config.search.title == "Software Engineer"
    assert config.search.location == "San Francisco"
    assert config.search.remote_only is True
    assert config.profile.file == "./profile.yaml"
    assert config.profile.resume == "./resume.pdf"
    assert config.notifications.desktop is True


def test_load_config_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/config.yaml")


def test_load_config_invalid_yaml(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("{{invalid yaml")
    with pytest.raises(ValueError):
        load_config(str(config_file))
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd /Users/shenghuang/Desktop/Projects/job_applier && python -m pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'job_applier'`

- [ ] **Step 5: Implement config.py**

```python
# src/job_applier/config.py
"""Configuration loading and validation."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class LLMConfig:
    provider: str = "ollama"
    model: str = "llama3"
    api_url: str = "http://localhost:11434"
    api_key: str = ""


@dataclass
class SearchConfig:
    title: str = ""
    location: str = ""
    remote_only: bool = False


@dataclass
class ProfileConfig:
    file: str = "./profile.yaml"
    resume: str = "./resume.pdf"


@dataclass
class NotificationConfig:
    desktop: bool = True
    log_file: str = "./logs/applications.jsonl"


@dataclass
class Config:
    llm: LLMConfig = field(default_factory=LLMConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    profile: ProfileConfig = field(default_factory=ProfileConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)


def _parse_config(data: dict[str, Any]) -> Config:
    """Parse raw YAML dict into Config dataclass."""
    llm_data = data.get("llm", {})
    search_data = data.get("search", {})
    profile_data = data.get("profile", {})
    notif_data = data.get("notifications", {})

    return Config(
        llm=LLMConfig(
            provider=llm_data.get("provider", "ollama"),
            model=llm_data.get("model", "llama3"),
            api_url=llm_data.get("api_url", "http://localhost:11434"),
            api_key=llm_data.get("api_key", ""),
        ),
        search=SearchConfig(
            title=search_data.get("title", ""),
            location=search_data.get("location", ""),
            remote_only=search_data.get("remote_only", False),
        ),
        profile=ProfileConfig(
            file=profile_data.get("file", "./profile.yaml"),
            resume=profile_data.get("resume", "./resume.pdf"),
        ),
        notifications=NotificationConfig(
            desktop=notif_data.get("desktop", True),
            log_file=notif_data.get("log_file", "./logs/applications.jsonl"),
        ),
    )


def load_config(path: str) -> Config:
    """Load config from a YAML file."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(file_path) as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}") from e

    if not isinstance(data, dict):
        raise ValueError("Config file must contain a YAML mapping")

    return _parse_config(data)
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd /Users/shenghuang/Desktop/Projects/job_applier && PYTHONPATH=src python -m pytest tests/test_config.py -v`
Expected: 3 passed

- [ ] **Step 7: Create example config.yaml**

```yaml
llm:
  provider: ollama
  model: llama3
  api_url: http://localhost:11434
  api_key: ""

search:
  title: "Software Engineer"
  location: "San Francisco"
  remote_only: true

profile:
  file: ./profile.yaml
  resume: ./resume.pdf

notifications:
  desktop: true
  log_file: ./logs/applications.jsonl
```

- [ ] **Step 8: Create example profile.yaml**

```yaml
name: "Your Name"
email: "your@email.com"
phone: "+1-555-123-4567"
location: "San Francisco, CA"
linkedin: "linkedin.com/in/yourname"

work_history:
  - company: "Previous Company"
    title: "Software Engineer"
    duration: "2 years"
    description: "Built X, Y, Z"

education:
  - school: "University of California"
    degree: "BS Computer Science"
    year: "2020"

skills:
  - Python
  - JavaScript
  - React

screening_answers:
  years_experience: "5"
  visa_status: "US Citizen"
  willing_to_relocate: "Yes"
  salary_expectation: "120000"
```

- [ ] **Step 9: Commit**

```bash
git add pyproject.toml src/job_applier/__init__.py src/job_applier/config.py tests/__init__.py tests/test_config.py config.yaml profile.yaml
git commit -m "feat: project setup with config loading and validation"
```

---

### Task 2: Camoufox Browser Client

**Files:**
- Create: `src/job_applier/browser.py`
- Create: `tests/test_browser.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_browser.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from job_applier.browser import CamoufoxClient


@pytest.fixture
def client():
    return CamoufoxClient(base_url="http://localhost:3000")


def test_client_init():
    client = CamoufoxClient(base_url="http://localhost:3000")
    assert client.base_url == "http://localhost:3000"


@pytest.mark.asyncio
async def test_create_tab(client):
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"tabId": "abc123", "url": "about:blank"}

    with patch.object(client, "_request", new_callable=AsyncMock, return_value=mock_response):
        tab = await client.create_tab("https://example.com")
        assert tab["tabId"] == "abc123"


@pytest.mark.asyncio
async def test_close_tab(client):
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch.object(client, "_request", new_callable=AsyncMock, return_value=mock_response):
        result = await client.close_tab("abc123")
        assert result is True


@pytest.mark.asyncio
async def test_click_element(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "clicked"}

    with patch.object(client, "_request", new_callable=AsyncMock, return_value=mock_response):
        result = await client.click("abc123", "button 'Submit'")
        assert result["status"] == "clicked"


@pytest.mark.asyncio
async def test_fill_field(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "filled"}

    with patch.object(client, "_request", new_callable=AsyncMock, return_value=mock_response):
        result = await client.fill("abc123", "textbox 'First Name'", "John")
        assert result["status"] == "filled"


@pytest.mark.asyncio
async def test_get_snapshot(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "snapshot": "textbox 'First Name'\ntextbox 'Email'\nbutton 'Submit'"
    }

    with patch.object(client, "_request", new_callable=AsyncMock, return_value=mock_response):
        snapshot = await client.get_snapshot("abc123")
        assert "textbox 'First Name'" in snapshot


@pytest.mark.asyncio
async def test_navigate(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"url": "https://example.com"}

    with patch.object(client, "_request", new_callable=AsyncMock, return_value=mock_response):
        result = await client.navigate("abc123", "https://example.com")
        assert result["url"] == "https://example.com"


@pytest.mark.asyncio
async def test_upload_file(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "uploaded"}

    with patch.object(client, "_request", new_callable=AsyncMock, return_value=mock_response):
        result = await client.upload_file("abc123", "upload 'Resume'", "/path/to/resume.pdf")
        assert result["status"] == "uploaded"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/shenghuang/Desktop/Projects/job_applier && PYTHONPATH=src python -m pytest tests/test_browser.py -v`
Expected: FAIL with `ImportError: cannot import name 'CamoufoxClient'`

- [ ] **Step 3: Implement browser.py**

```python
# src/job_applier/browser.py
"""Camoufox REST API client for browser automation."""
from __future__ import annotations

import httpx


class CamoufoxClient:
    """Client for the Camoufox browser REST API."""

    def __init__(self, base_url: str = "http://localhost:3000", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._http = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        return await self._http.request(method, path, **kwargs)

    async def create_tab(self, url: str = "about:blank") -> dict:
        """Open a new browser tab."""
        resp = await self._request("POST", "/tabs", json={"url": url})
        resp.raise_for_status()
        return resp.json()

    async def close_tab(self, tab_id: str) -> bool:
        """Close a browser tab."""
        resp = await self._request("DELETE", f"/tabs/{tab_id}")
        resp.raise_for_status()
        return True

    async def navigate(self, tab_id: str, url: str) -> dict:
        """Navigate a tab to a URL."""
        resp = await self._request("POST", f"/tabs/{tab_id}/navigate", json={"url": url})
        resp.raise_for_status()
        return resp.json()

    async def get_snapshot(self, tab_id: str) -> str:
        """Get accessibility snapshot of the current page."""
        resp = await self._request("GET", f"/tabs/{tab_id}/snapshot")
        resp.raise_for_status()
        data = resp.json()
        return data.get("snapshot", "")

    async def click(self, tab_id: str, selector: str) -> dict:
        """Click an element by accessibility selector."""
        resp = await self._request("POST", f"/tabs/{tab_id}/click", json={"selector": selector})
        resp.raise_for_status()
        return resp.json()

    async def fill(self, tab_id: str, selector: str, value: str) -> dict:
        """Fill a form field with a value."""
        resp = await self._request("POST", f"/tabs/{tab_id}/fill", json={"selector": selector, "value": value})
        resp.raise_for_status()
        return resp.json()

    async def upload_file(self, tab_id: str, selector: str, file_path: str) -> dict:
        """Upload a file to a file input field."""
        resp = await self._request("POST", f"/tabs/{tab_id}/upload", json={"selector": selector, "path": file_path})
        resp.raise_for_status()
        return resp.json()

    async def select_option(self, tab_id: str, selector: str, value: str) -> dict:
        """Select an option from a dropdown."""
        resp = await self._request("POST", f"/tabs/{tab_id}/select", json={"selector": selector, "value": value})
        resp.raise_for_status()
        return resp.json()

    async def get_url(self, tab_id: str) -> str:
        """Get the current URL of a tab."""
        resp = await self._request("GET", f"/tabs/{tab_id}/url")
        resp.raise_for_status()
        return resp.json().get("url", "")

    async def get_title(self, tab_id: str) -> str:
        """Get the current page title."""
        resp = await self._request("GET", f"/tabs/{tab_id}/title")
        resp.raise_for_status()
        return resp.json().get("title", "")

    async def wait_for_navigation(self, tab_id: str, timeout: float = 10.0) -> str:
        """Wait for navigation to complete and return new URL."""
        resp = await self._request("POST", f"/tabs/{tab_id}/wait-navigation", json={"timeout": timeout})
        resp.raise_for_status()
        return resp.json().get("url", "")

    async def close(self):
        """Close the HTTP client."""
        await self._http.aclose()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/shenghuang/Desktop/Projects/job_applier && PYTHONPATH=src python -m pytest tests/test_browser.py -v`
Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add src/job_applier/browser.py tests/test_browser.py
git commit -m "feat: Camoufox REST API client"
```

---

### Task 3: LLM Provider Abstraction

**Files:**
- Create: `src/job_applier/llm.py`
- Create: `tests/test_llm.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/shenghuang/Desktop/Projects/job_applier && PYTHONPATH=src python -m pytest tests/test_llm.py -v`
Expected: FAIL with `ImportError: cannot import name 'LLMProvider'`

- [ ] **Step 3: Implement llm.py**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/shenghuang/Desktop/Projects/job_applier && PYTHONPATH=src python -m pytest tests/test_llm.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/job_applier/llm.py tests/test_llm.py
git commit -m "feat: LLM provider abstraction (Ollama, OpenAI, Anthropic)"
```

---

### Task 4: Prompt Building & Response Parsing

**Files:**
- Create: `src/job_applier/prompt.py`
- Create: `tests/test_prompt.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_prompt.py
import json
import pytest
from job_applier.prompt import build_form_filling_prompt, build_account_creation_prompt, parse_llm_response


SAMPLE_PROFILE = {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-123-4567",
    "location": "San Francisco, CA",
    "work_history": [
        {"company": "Acme Corp", "title": "Engineer", "duration": "3 years", "description": "Built things"}
    ],
    "education": [
        {"school": "UC Berkeley", "degree": "BS CS", "year": "2020"}
    ],
    "skills": ["Python", "JavaScript"],
    "screening_answers": {
        "years_experience": "5",
        "visa_status": "US Citizen",
    },
}


def test_build_form_filling_prompt():
    snapshot = "textbox 'First Name'\ntextbox 'Email'\nbutton 'Submit'"
    job_desc = "Software Engineer at Acme Corp"
    prompt = build_form_filling_prompt(snapshot, SAMPLE_PROFILE, job_desc, resume_text="5 years experience")
    assert "textbox 'First Name'" in prompt
    assert "John Doe" in prompt
    assert "Software Engineer at Acme Corp" in prompt
    assert "JSON" in prompt


def test_build_account_creation_prompt():
    snapshot = "textbox 'Email'\ntextbox 'Password'\nbutton 'Create Account'"
    prompt = build_account_creation_prompt(snapshot, SAMPLE_PROFILE, "workday.com")
    assert "workday.com" in prompt
    assert "Create Account" in prompt
    assert "JSON" in prompt


def test_parse_llm_response_valid():
    response = {
        "fields": [
            {"selector": "textbox 'First Name'", "value": "John"},
            {"selector": "textbox 'Email'", "value": "john@example.com"},
        ],
        "click": "button 'Submit'",
        "status": "continue",
    }
    result = parse_llm_response(response)
    assert len(result["fields"]) == 2
    assert result["click"] == "button 'Submit'"
    assert result["status"] == "continue"


def test_parse_llm_response_account_creation():
    response = {
        "fields": [
            {"selector": "textbox 'Email'", "value": "john+workday@example.com"},
            {"selector": "textbox 'Password'", "value": "Str0ngP@ss!123"},
        ],
        "click": "button 'Create Account'",
        "status": "account_created",
        "account": {"email": "john+workday@example.com", "password": "Str0ngP@ss!123"},
    }
    result = parse_llm_response(response)
    assert result["status"] == "account_created"
    assert result["account"]["email"] == "john+workday@example.com"


def test_parse_llm_response_done():
    response = {"fields": [], "click": None, "status": "done"}
    result = parse_llm_response(response)
    assert result["status"] == "done"
    assert result["fields"] == []


def test_parse_llm_response_missing_keys():
    response = {"fields": []}
    result = parse_llm_response(response)
    assert result["click"] is None
    assert result["status"] == "unknown"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/shenghuang/Desktop/Projects/job_applier && PYTHONPATH=src python -m pytest tests/test_prompt.py -v`
Expected: FAIL with `ImportError: cannot import name 'build_form_filling_prompt'`

- [ ] **Step 3: Implement prompt.py**

```python
# src/job_applier/prompt.py
"""Prompt building and LLM response parsing for form filling."""
from __future__ import annotations

from typing import Any


def _format_profile(profile: dict[str, Any]) -> str:
    """Format profile data into a concise string for the LLM prompt."""
    lines = []
    for key in ("name", "email", "phone", "location", "linkedin"):
        if key in profile:
            lines.append(f"{key}: {profile[key]}")

    if "work_history" in profile:
        lines.append("\nWork History:")
        for job in profile["work_history"]:
            lines.append(f"  - {job.get('title', '')} at {job.get('company', '')} ({job.get('duration', '')})")
            if job.get("description"):
                lines.append(f"    {job['description']}")

    if "education" in profile:
        lines.append("\nEducation:")
        for edu in profile["education"]:
            lines.append(f"  - {edu.get('degree', '')} from {edu.get('school', '')} ({edu.get('year', '')})")

    if "skills" in profile:
        lines.append(f"\nSkills: {', '.join(profile['skills'])}")

    if "screening_answers" in profile:
        lines.append("\nScreening Answers:")
        for key, val in profile["screening_answers"].items():
            lines.append(f"  {key}: {val}")

    return "\n".join(lines)


def build_form_filling_prompt(
    snapshot: str,
    profile: dict[str, Any],
    job_description: str,
    resume_text: str = "",
) -> str:
    """Build a prompt for the LLM to fill form fields."""
    profile_text = _format_profile(profile)

    return f"""You are an AI assistant filling out a job application form.

PAGE ACCESSIBILITY SNAPSHOT:
{snapshot}

YOUR PROFILE:
{profile_text}

{f'RESUME TEXT: {resume_text}' if resume_text else ''}

JOB DESCRIPTION:
{job_description}

Based on the page snapshot and your profile, determine what to fill in each field and what button to click next.

IMPORTANT RULES:
1. For file upload fields (like "upload 'Resume'"), use action "upload_file" with the resume path
2. For dropdown fields, use the exact option text that matches from the snapshot
3. For radio buttons and checkboxes, select the most appropriate option
4. For screening questions, use values from the profile's screening_answers when available
5. For questions not in screening_answers, answer based on the profile info (e.g., use work_history for experience questions)

Return ONLY a JSON object with this exact structure:
{{
  "fields": [
    {{"selector": "the exact selector from snapshot", "value": "what to fill in"}}
  ],
  "click": "the exact selector of the button to click, or null if form is complete",
  "status": "continue" | "done" | "needs_user_input" | "error"
}}

If you cannot determine what to fill in a field, set status to "needs_user_input" and explain what you need in a "message" field."""


def build_account_creation_prompt(
    snapshot: str,
    profile: dict[str, Any],
    site_domain: str,
) -> str:
    """Build a prompt for the LLM to create an account on an external site."""
    profile_text = _format_profile(profile)

    return f"""You are an AI assistant creating an account on an external job application site.

SITE DOMAIN: {site_domain}

PAGE ACCESSIBILITY SNAPSHOT:
{snapshot}

YOUR PROFILE:
{profile_text}

Based on the page snapshot and your profile, fill in the signup form fields.

RULES:
1. For email: use the profile email, or a variation like "name+sitedomain@gmail.com" if needed
2. For password: generate a strong random password (16+ chars, mix of letters, numbers, symbols)
3. For name fields: use the profile name
4. For any other fields: use appropriate profile data

Return ONLY a JSON object with this exact structure:
{{
  "fields": [
    {{"selector": "the exact selector from snapshot", "value": "what to fill in"}}
  ],
  "click": "the exact selector of the submit/create button",
  "status": "account_created",
  "account": {{"email": "the email used", "password": "the password generated"}}
}}"""


def parse_llm_response(response: dict[str, Any]) -> dict[str, Any]:
    """Parse and validate LLM response into structured form-filling actions."""
    fields = response.get("fields", [])
    click = response.get("click")
    status = response.get("status", "unknown")
    account = response.get("account")
    message = response.get("message")

    result: dict[str, Any] = {
        "fields": fields,
        "click": click,
        "status": status,
    }

    if account:
        result["account"] = account
    if message:
        result["message"] = message

    return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/shenghuang/Desktop/Projects/job_applier && PYTHONPATH=src python -m pytest tests/test_prompt.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add src/job_applier/prompt.py tests/test_prompt.py
git commit -m "feat: prompt building and LLM response parsing"
```

---

### Task 5: Account Manager

**Files:**
- Create: `src/job_applier/accounts.py`
- Create: `tests/test_accounts.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_accounts.py
import pytest
from job_applier.accounts import AccountManager


@pytest.fixture
def manager(tmp_path):
    db_path = str(tmp_path / "accounts.db")
    return AccountManager(db_path)


def test_init_creates_db(manager):
    assert manager is not None


def test_store_account(manager):
    manager.store("workday.com", "john+workday@example.com", "Str0ngP@ss!123")
    account = manager.get("workday.com")
    assert account is not None
    assert account["email"] == "john+workday@example.com"
    assert account["password"] == "Str0ngP@ss!123"
    assert account["domain"] == "workday.com"


def test_get_nonexistent_account(manager):
    account = manager.get("nonexistent.com")
    assert account is None


def test_store_multiple_accounts(manager):
    manager.store("workday.com", "john+workday@example.com", "pass1")
    manager.store("greenhouse.io", "john+greenhouse@example.com", "pass2")

    assert manager.get("workday.com")["email"] == "john+workday@example.com"
    assert manager.get("greenhouse.io")["email"] == "john+greenhouse@example.com"


def test_update_existing_account(manager):
    manager.store("workday.com", "john+workday@example.com", "old_pass")
    manager.store("workday.com", "john+workday@example.com", "new_pass")

    account = manager.get("workday.com")
    assert account["password"] == "new_pass"


def test_list_all_accounts(manager):
    manager.store("workday.com", "a@b.com", "p1")
    manager.store("greenhouse.io", "c@d.com", "p2")
    manager.store("lever.co", "e@f.com", "p3")

    accounts = manager.list_all()
    assert len(accounts) == 3
    domains = {a["domain"] for a in accounts}
    assert domains == {"workday.com", "greenhouse.io", "lever.co"}


def test_delete_account(manager):
    manager.store("workday.com", "a@b.com", "p1")
    manager.delete("workday.com")
    assert manager.get("workday.com") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/shenghuang/Desktop/Projects/job_applier && PYTHONPATH=src python -m pytest tests/test_accounts.py -v`
Expected: FAIL with `ImportError: cannot import name 'AccountManager'`

- [ ] **Step 3: Implement accounts.py**

```python
# src/job_applier/accounts.py
"""Account manager for storing external site credentials."""
from __future__ import annotations

import sqlite3
from typing import Any, Optional


class AccountManager:
    """Manages stored credentials for external ATS accounts."""

    def __init__(self, db_path: str = "accounts.db"):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                domain TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._conn.commit()

    def store(self, domain: str, email: str, password: str) -> None:
        """Store or update credentials for a domain."""
        self._conn.execute(
            "INSERT OR REPLACE INTO accounts (domain, email, password) VALUES (?, ?, ?)",
            (domain, email, password),
        )
        self._conn.commit()

    def get(self, domain: str) -> Optional[dict[str, Any]]:
        """Get credentials for a domain, or None if not found."""
        row = self._conn.execute("SELECT * FROM accounts WHERE domain = ?", (domain,)).fetchone()
        if row is None:
            return None
        return dict(row)

    def list_all(self) -> list[dict[str, Any]]:
        """List all stored accounts."""
        rows = self._conn.execute("SELECT * FROM accounts").fetchall()
        return [dict(row) for row in rows]

    def delete(self, domain: str) -> None:
        """Delete credentials for a domain."""
        self._conn.execute("DELETE FROM accounts WHERE domain = ?", (domain,))
        self._conn.commit()

    def close(self):
        self._conn.close()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/shenghuang/Desktop/Projects/job_applier && PYTHONPATH=src python -m pytest tests/test_accounts.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add src/job_applier/accounts.py tests/test_accounts.py
git commit -m "feat: account manager with SQLite storage"
```

---

### Task 6: Notification System

**Files:**
- Create: `src/job_applier/notifications.py`
- Create: `tests/test_notifications.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_notifications.py
import json
import os
import pytest
from unittest.mock import patch, MagicMock
from job_applier.notifications import NotificationSystem


@pytest.fixture
def system(tmp_path):
    log_file = str(tmp_path / "applications.jsonl")
    return NotificationSystem(log_file=log_file, desktop=False)


def test_init_creates_log_dir(tmp_path):
    log_file = str(tmp_path / "subdir" / "apps.jsonl")
    system = NotificationSystem(log_file=log_file, desktop=False)
    assert os.path.exists(tmp_path / "subdir")


def test_log_application(system):
    system.log_application(
        job_title="Software Engineer",
        company="Acme Corp",
        url="https://example.com/apply",
        status="applied",
    )

    with open(system.log_file) as f:
        lines = f.readlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["job_title"] == "Software Engineer"
    assert entry["company"] == "Acme Corp"
    assert entry["status"] == "applied"


def test_log_account_created(system):
    system.log_application(
        job_title="Software Engineer",
        company="Acme Corp",
        url="https://example.com/apply",
        status="applied",
        account_created=True,
        account_email="john+acme@example.com",
        account_password="Str0ngP@ss",
    )

    with open(system.log_file) as f:
        entry = json.loads(f.readline())
    assert entry["account_created"] is True
    assert entry["account_email"] == "john+acme@example.com"


def test_log_error(system):
    system.log_application(
        job_title="Software Engineer",
        company="Acme Corp",
        url="https://example.com/apply",
        status="error",
        error="Bot detection triggered",
    )

    with open(system.log_file) as f:
        entry = json.loads(f.readline())
    assert entry["status"] == "error"
    assert entry["error"] == "Bot detection triggered"


def test_desktop_notification():
    system = NotificationSystem(log_file="/dev/null", desktop=True)
    with patch("job_applier.notifications.notify") as mock_notify:
        system.send_desktop("Applied to Software Engineer at Acme Corp")
        mock_notify.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/shenghuang/Desktop/Projects/job_applier && PYTHONPATH=src python -m pytest tests/test_notifications.py -v`
Expected: FAIL with `ImportError: cannot import name 'NotificationSystem'`

- [ ] **Step 3: Implement notifications.py**

```python
# src/job_applier/notifications.py
"""Notification system for job applications."""
from __future__ import annotations

import json
import os
import logging
from datetime import datetime, timezone
from typing import Any, Optional

try:
    from plyer import notification as plyer_notification

    def notify(title: str, message: str):
        plyer_notification.notify(title=title, message=message, timeout=10)

except ImportError:
    def notify(title: str, message: str):
        logging.getLogger(__name__).warning("Desktop notifications unavailable (install plyer)")

logger = logging.getLogger(__name__)


class NotificationSystem:
    """Handles desktop notifications and application logging."""

    def __init__(self, log_file: str = "./logs/applications.jsonl", desktop: bool = True):
        self.log_file = log_file
        self.desktop = desktop
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)

    def log_application(
        self,
        job_title: str,
        company: str,
        url: str,
        status: str,
        account_created: bool = False,
        account_email: str = "",
        account_password: str = "",
        error: str = "",
    ) -> None:
        """Log a job application to the JSONL file."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "job_title": job_title,
            "company": company,
            "url": url,
            "status": status,
        }

        if account_created:
            entry["account_created"] = True
            entry["account_email"] = account_email
            entry["account_password"] = account_password

        if error:
            entry["error"] = error

        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

        logger.info("Logged application: %s at %s — %s", job_title, company, status)

    def send_desktop(self, message: str, title: str = "Job Applier") -> None:
        """Send a desktop notification."""
        if self.desktop:
            notify(title=title, message=message)

    def notify_application(
        self,
        job_title: str,
        company: str,
        account_created: bool = False,
        account_email: str = "",
        account_password: str = "",
    ) -> None:
        """Send a notification for a completed application."""
        msg = f"Applied to {job_title} at {company}"
        if account_created:
            msg += f"\nAccount created: {account_email}"
            msg += f"\nPassword: {account_password}"

        self.send_desktop(msg)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/shenghuang/Desktop/Projects/job_applier && PYTHONPATH=src python -m pytest tests/test_notifications.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/job_applier/notifications.py tests/test_notifications.py
git commit -m "feat: notification system with desktop notifications and JSONL logging"
```

---

### Task 7: Indeed Job Search Engine

**Files:**
- Create: `src/job_applier/search.py`
- Create: `tests/test_search.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_search.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from job_applier.search import IndeedSearcher


@pytest.fixture
def browser():
    return MagicMock()


@pytest.fixture
def searcher(browser):
    return IndeedSearcher(browser)


def test_init(searcher):
    assert searcher is not None


@pytest.mark.asyncio
async def test_parse_job_listings():
    from job_applier.search import _parse_job_listings

    snapshot = """
link "Software Engineer at Acme Corp" [ref=e1]
text "San Francisco, CA"
text "$120,000 - $150,000 a year"
link "Apply now" [ref=e2]

link "Backend Developer at Beta Inc" [ref=e3]
text "Remote"
text "$100,000 - $130,000 a year"
link "Apply now" [ref=e4]
"""
    jobs = _parse_job_listings(snapshot)
    assert len(jobs) == 2
    assert jobs[0]["title"] == "Software Engineer at Acme Corp"
    assert jobs[0]["company"] == "Acme Corp"
    assert jobs[1]["title"] == "Backend Developer at Beta Inc"
    assert jobs[1]["company"] == "Beta Inc"


@pytest.mark.asyncio
async def test_search_returns_jobs(searcher):
    mock_snapshot = """
link "Software Engineer at Acme Corp" [ref=e1]
text "San Francisco, CA"
link "Apply now" [ref=e2]
"""
    with patch.object(searcher.browser, "get_snapshot", new_callable=AsyncMock, return_value=mock_snapshot):
        with patch.object(searcher.browser, "navigate", new_callable=AsyncMock):
            with patch.object(searcher.browser, "click", new_callable=AsyncMock):
                with patch.object(searcher.browser, "fill", new_callable=AsyncMock):
                    with patch("asyncio.sleep", new_callable=AsyncMock):
                        jobs = await searcher.search("Software Engineer", "San Francisco")
                        assert len(jobs) >= 1
                        assert jobs[0]["title"] == "Software Engineer at Acme Corp"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/shenghuang/Desktop/Projects/job_applier && PYTHONPATH=src python -m pytest tests/test_search.py -v`
Expected: FAIL with `ImportError: cannot import name 'IndeedSearcher'`

- [ ] **Step 3: Implement search.py**

```python
# src/job_applier/search.py
"""Indeed job search engine."""
from __future__ import annotations

import asyncio
import logging
import random
import re
from typing import Any

from job_applier.browser import CamoufoxClient

logger = logging.getLogger(__name__)

INDEED_URL = "https://www.indeed.com"


def _parse_job_listings(snapshot: str) -> list[dict[str, str]]:
    """Parse job listings from an accessibility snapshot."""
    jobs = []
    lines = snapshot.strip().split("\n")
    current_job: dict[str, str] = {}

    for line in lines:
        line = line.strip()
        if not line:
            if current_job.get("title"):
                jobs.append(current_job)
                current_job = {}
            continue

        # Match job title links: link "Job Title at Company" [ref=...]
        title_match = re.search(r'link\s+"(.+? at .+?)"', line)
        if title_match:
            if current_job.get("title"):
                jobs.append(current_job)
            full_title = title_match.group(1)
            parts = full_title.rsplit(" at ", 1)
            current_job = {
                "title": parts[0].strip() if len(parts) > 1 else full_title,
                "company": parts[1].strip() if len(parts) > 1 else "",
                "location": "",
                "salary": "",
                "apply_ref": "",
            }
            continue

        # Match location
        if "text" in line and not current_job.get("location"):
            loc_match = re.search(r'text\s+"([^"]+)"', line)
            if loc_match:
                loc = loc_match.group(1)
                if not any(c.isdigit() for c in loc) or "CA" in loc or "Remote" in loc:
                    current_job["location"] = loc

        # Match salary
        if "text" in line and ("$" in line or "year" in line or "hour" in line):
            sal_match = re.search(r'text\s+"([^"]*(?:\$|year|hour)[^"]*)"', line)
            if sal_match:
                current_job["salary"] = sal_match.group(1)

        # Match apply link
        if "Apply" in line and "ref=" in line:
            apply_match = ref_match = re.search(r'ref=(\w+)', line)
            if apply_match:
                current_job["apply_ref"] = apply_match.group(1)

    if current_job.get("title"):
        jobs.append(current_job)

    return jobs


class IndeedSearcher:
    """Searches Indeed for job listings."""

    def __init__(self, browser: CamoufoxClient):
        self.browser = browser

    async def search(
        self,
        title: str,
        location: str = "",
        max_pages: int = 3,
    ) -> list[dict[str, str]]:
        """Search Indeed and return job listings."""
        tab = await self.browser.create_tab(INDEED_URL)
        tab_id = tab["tabId"]

        try:
            # Build search URL
            search_url = f"{INDEED_URL}/jobs?q={title.replace(' ', '+')}"
            if location:
                search_url += f"&l={location.replace(' ', '+')}"

            await self.browser.navigate(tab_id, search_url)
            await asyncio.sleep(random.uniform(2, 4))

            all_jobs: list[dict[str, str]] = []

            for page in range(max_pages):
                snapshot = await self.browser.get_snapshot(tab_id)
                jobs = _parse_job_listings(snapshot)
                all_jobs.extend(jobs)
                logger.info("Page %d: found %d jobs", page + 1, len(jobs))

                # Try to go to next page
                if page < max_pages - 1:
                    try:
                        next_ref = re.search(r'link\s+"Next"\s+\[ref=(\w+)\]', snapshot)
                        if next_ref:
                            await self.browser.click(tab_id, f"link 'Next' [ref={next_ref.group(1)}]")
                            await asyncio.sleep(random.uniform(2, 5))
                        else:
                            break
                    except Exception:
                        break

            return all_jobs

        finally:
            await self.browser.close_tab(tab_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/shenghuang/Desktop/Projects/job_applier && PYTHONPATH=src python -m pytest tests/test_search.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/job_applier/search.py tests/test_search.py
git commit -m "feat: Indeed job search engine with listing parser"
```

---

### Task 8: Application Engine (AI-First Form Filler)

**Files:**
- Create: `src/job_applier/application.py`
- Create: `tests/test_application.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_application.py
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from job_applier.application import ApplicationEngine


@pytest.fixture
def browser():
    return MagicMock()


@pytest.fixture
def llm():
    return MagicMock()


@pytest.fixture
def accounts():
    return MagicMock()


@pytest.fixture
def notifications():
    return MagicMock()


@pytest.fixture
def engine(browser, llm, accounts, notifications):
    return ApplicationEngine(
        browser=browser,
        llm=llm,
        accounts=accounts,
        notifications=notifications,
        profile={"name": "John", "email": "john@example.com"},
        resume_path="/path/to/resume.pdf",
    )


@pytest.mark.asyncio
async def test_fill_fields(engine):
    engine.browser.fill = AsyncMock(return_value={"status": "filled"})

    fields = [
        {"selector": "textbox 'First Name'", "value": "John"},
        {"selector": "textbox 'Email'", "value": "john@example.com"},
    ]
    await engine._fill_fields("tab123", fields)
    assert engine.browser.fill.call_count == 2


@pytest.mark.asyncio
async def test_click_button(engine):
    engine.browser.click = AsyncMock(return_value={"status": "clicked"})
    await engine._click_button("tab123", "button 'Submit'")
    engine.browser.click.assert_called_once_with("tab123", "button 'Submit'")


@pytest.mark.asyncio
async def test_upload_resume(engine):
    engine.browser.upload_file = AsyncMock(return_value={"status": "uploaded"})
    fields = [{"selector": "upload 'Resume'", "action": "upload_file", "path": "/path/to/resume.pdf"}]
    await engine._fill_fields("tab123", fields)
    engine.browser.upload_file.assert_called_once_with("tab123", "upload 'Resume'", "/path/to/resume.pdf")


@pytest.mark.asyncio
async def test_detect_account_creation(engine):
    assert engine._detect_account_creation("workday.com", "Sign up for Workday") is True
    assert engine._detect_account_creation("indeed.com", "Apply now") is False
    assert engine._detect_account_creation("greenhouse.io", "Create account") is True


@pytest.mark.asyncio
async def test_handle_account_creation(engine):
    engine.browser.get_snapshot = AsyncMock(return_value="textbox 'Email'\nbutton 'Create Account'")
    engine.browser.fill = AsyncMock(return_value={"status": "filled"})
    engine.browser.click = AsyncMock(return_value={"status": "clicked"})
    engine.browser.get_url = AsyncMock(return_value="https://apply.workday.com/signup")
    engine.accounts.get.return_value = None
    engine.accounts.store = MagicMock()
    engine.llm.generate = AsyncMock(return_value={
        "fields": [
            {"selector": "textbox 'Email'", "value": "john+workday@example.com"},
            {"selector": "textbox 'Password'", "value": "Str0ngP@ss"},
        ],
        "click": "button 'Create Account'",
        "status": "account_created",
        "account": {"email": "john+workday@example.com", "password": "Str0ngP@ss"},
    })

    result = await engine._handle_account_creation("tab123", "workday.com")
    assert result is True
    engine.accounts.store.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/shenghuang/Desktop/Projects/job_applier && PYTHONPATH=src python -m pytest tests/test_application.py -v`
Expected: FAIL with `ImportError: cannot import name 'ApplicationEngine'`

- [ ] **Step 3: Implement application.py**

```python
# src/job_applier/application.py
"""AI-first application engine for filling job forms."""
from __future__ import annotations

import asyncio
import logging
import random
import re
from typing import Any, Optional
from urllib.parse import urlparse

from job_applier.browser import CamoufoxClient
from job_applier.llm import LLMProvider
from job_applier.accounts import AccountManager
from job_applier.notifications import NotificationSystem
from job_applier.prompt import build_form_filling_prompt, build_account_creation_prompt, parse_llm_response

logger = logging.getLogger(__name__)

MAX_PAGES = 20
ACCOUNT_DOMAINS = ("workday.com", "greenhouse.io", "lever.co", "ashbyhq.com", "icims.com", "smartrecruiters.com")


class ApplicationEngine:
    """Fills job application forms using AI."""

    def __init__(
        self,
        browser: CamoufoxClient,
        llm: LLMProvider,
        accounts: AccountManager,
        notifications: NotificationSystem,
        profile: dict[str, Any],
        resume_path: str = "",
    ):
        self.browser = browser
        self.llm = llm
        self.accounts = accounts
        self.notifications = notifications
        self.profile = profile
        self.resume_path = resume_path

    def _detect_account_creation(self, domain: str, page_title: str = "") -> bool:
        """Check if the page requires account creation."""
        page_lower = page_title.lower()
        keywords = ("sign up", "create account", "register", "join", "new account")
        return any(kw in page_lower for kw in keywords)

    def _extract_domain(self, url: str) -> str:
        """Extract the base domain from a URL."""
        parsed = urlparse(url)
        host = parsed.hostname or ""
        # Remove www. prefix
        if host.startswith("www."):
            host = host[4:]
        return host

    async def _fill_fields(self, tab_id: str, fields: list[dict[str, str]]) -> None:
        """Fill form fields using the browser."""
        for field in fields:
            selector = field.get("selector", "")
            value = field.get("value", "")
            action = field.get("action", "")

            if action == "upload_file" or "upload" in selector.lower():
                path = field.get("path", self.resume_path)
                await self.browser.upload_file(tab_id, selector, path)
            elif value:
                await self.browser.fill(tab_id, selector, value)

            await asyncio.sleep(random.uniform(0.3, 0.8))

    async def _click_button(self, tab_id: str, selector: str) -> None:
        """Click a button."""
        if selector:
            await self.browser.click(tab_id, selector)

    async def _handle_account_creation(self, tab_id: str, domain: str) -> bool:
        """Handle account creation on an external site."""
        # Check if we already have an account
        existing = self.accounts.get(domain)
        if existing:
            logger.info("Using existing account for %s", domain)
            return True

        snapshot = await self.browser.get_snapshot(tab_id)
        prompt = build_account_creation_prompt(snapshot, self.profile, domain)
        response = await self.llm.generate(prompt)
        parsed = parse_llm_response(response)

        if parsed.get("status") == "account_created" and parsed.get("account"):
            await self._fill_fields(tab_id, parsed["fields"])
            if parsed.get("click"):
                await self._click_button(tab_id, parsed["click"])
            account = parsed["account"]
            self.accounts.store(domain, account["email"], account["password"])
            self.notifications.send_desktop(
                f"Account created on {domain}\nEmail: {account['email']}\nPassword: {account['password']}"
            )
            return True

        return False

    async def apply_to_job(self, tab_id: str, job: dict[str, str]) -> dict[str, Any]:
        """Fill out a single job application form."""
        result = {"status": "unknown", "pages_filled": 0}

        try:
            for page_num in range(MAX_PAGES):
                snapshot = await self.browser.get_snapshot(tab_id)
                url = await self.browser.get_url(tab_id)
                domain = self._extract_domain(url)

                # Check if account creation is needed
                title_match = re.search(r'page "([^"]*)"', snapshot)
                page_title = title_match.group(1) if title_match else ""
                if self._detect_account_creation(domain, page_title):
                    created = await self._handle_account_creation(tab_id, domain)
                    if not created:
                        result["status"] = "account_creation_failed"
                        return result
                    # After account creation, take a fresh snapshot
                    continue

                # Build prompt and get LLM response
                prompt = build_form_filling_prompt(
                    snapshot,
                    self.profile,
                    job.get("description", job.get("title", "")),
                )
                response = await self.llm.generate(prompt)
                parsed = parse_llm_response(response)

                # Fill fields
                if parsed.get("fields"):
                    await self._fill_fields(tab_id, parsed["fields"])
                    result["pages_filled"] += 1

                # Check status
                status = parsed.get("status", "unknown")
                if status == "done":
                    result["status"] = "applied"
                    return result
                elif status == "needs_user_input":
                    result["status"] = "needs_input"
                    result["message"] = parsed.get("message", "")
                    return result
                elif status == "error":
                    result["status"] = "error"
                    result["message"] = parsed.get("message", "")
                    return result

                # Click next/submit button
                if parsed.get("click"):
                    prev_url = url
                    await self._click_button(tab_id, parsed["click"])
                    await asyncio.sleep(random.uniform(2, 4))

                    # Check if page changed (redirect)
                    new_url = await self.browser.get_url(tab_id)
                    if new_url != prev_url:
                        logger.info("Redirected: %s -> %s", prev_url, new_url)

            result["status"] = "max_pages_reached"
            return result

        except Exception as e:
            logger.error("Error applying to job: %s", e)
            result["status"] = "error"
            result["message"] = str(e)
            return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/shenghuang/Desktop/Projects/job_applier && PYTHONPATH=src python -m pytest tests/test_application.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/job_applier/application.py tests/test_application.py
git commit -m "feat: AI-first application engine with multi-page form filling"
```

---

### Task 9: Main Runner (Orchestrator)

**Files:**
- Create: `src/job_applier/runner.py`
- Create: `src/job_applier/__main__.py`

- [ ] **Step 1: Implement runner.py**

```python
# src/job_applier/runner.py
"""Main orchestrator that ties all components together."""
from __future__ import annotations

import asyncio
import logging
import yaml
from typing import Any

from job_applier.config import load_config, Config
from job_applier.browser import CamoufoxClient
from job_applier.llm import create_llm_provider
from job_applier.search import IndeedSearcher
from job_applier.application import ApplicationEngine
from job_applier.accounts import AccountManager
from job_applier.notifications import NotificationSystem

logger = logging.getLogger(__name__)


def load_profile(path: str) -> dict[str, Any]:
    """Load user profile from YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


class Runner:
    """Main orchestrator for the job application process."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config: Config = load_config(config_path)
        self.profile: dict[str, Any] = load_profile(self.config.profile.file)

        # Initialize components
        self.browser = CamoufoxClient()
        self.llm = create_llm_provider(
            provider=self.config.llm.provider,
            model=self.config.llm.model,
            api_url=self.config.llm.api_url,
            api_key=self.config.llm.api_key,
        )
        self.accounts = AccountManager()
        self.notifications = NotificationSystem(
            log_file=self.config.notifications.log_file,
            desktop=self.config.notifications.desktop,
        )
        self.searcher = IndeedSearcher(self.browser)
        self.engine = ApplicationEngine(
            browser=self.browser,
            llm=self.llm,
            accounts=self.accounts,
            notifications=self.notifications,
            profile=self.profile,
            resume_path=self.config.profile.resume,
        )

    async def run(self):
        """Run the full job application pipeline."""
        logger.info("Starting job search: %s in %s", self.config.search.title, self.config.search.location)

        # Search for jobs
        jobs = await self.searcher.search(
            title=self.config.search.title,
            location=self.config.search.location,
        )
        logger.info("Found %d jobs", len(jobs))

        if not jobs:
            logger.warning("No jobs found. Check your search criteria.")
            return

        # Apply to each job
        for i, job in enumerate(jobs, 1):
            logger.info("Applying to %d/%d: %s at %s", i, len(jobs), job["title"], job["company"])

            tab = await self.browser.create_tab()
            tab_id = tab["tabId"]

            try:
                result = await self.engine.apply_to_job(tab_id, job)

                self.notifications.log_application(
                    job_title=job["title"],
                    company=job["company"],
                    url=job.get("url", ""),
                    status=result["status"],
                    error=result.get("message", ""),
                )

                if result["status"] == "applied":
                    self.notifications.send_desktop(f"Applied to {job['title']} at {job['company']}")
                    logger.info("Successfully applied to %s", job["title"])
                elif result["status"] == "needs_input":
                    self.notifications.send_desktop(
                        f"Needs input for {job['title']}: {result.get('message', '')}"
                    )
                    logger.warning("Needs input for %s: %s", job["title"], result.get("message", ""))
                else:
                    logger.warning("Failed to apply to %s: %s", job["title"], result.get("message", "unknown"))

            except Exception as e:
                logger.error("Error applying to %s: %s", job["title"], e)
                self.notifications.log_application(
                    job_title=job["title"],
                    company=job["company"],
                    url=job.get("url", ""),
                    status="error",
                    error=str(e),
                )
            finally:
                await self.browser.close_tab(tab_id)

            # Delay between applications
            await asyncio.sleep(3)

    async def close(self):
        """Clean up resources."""
        await self.browser.close()
        await self.llm.close()
        self.accounts.close()
```

- [ ] **Step 2: Implement __main__.py**

```python
# src/job_applier/__main__.py
"""CLI entry point for the job applier."""
import asyncio
import logging
import sys

from job_applier.runner import Runner


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("job_applier.log"),
        ],
    )


def main():
    setup_logging()
    logger = logging.getLogger("job_applier")

    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    logger.info("Using config: %s", config_path)

    runner = Runner(config_path)
    try:
        asyncio.run(runner.run())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error("Fatal error: %s", e)
        sys.exit(1)
    finally:
        asyncio.run(runner.close())


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Verify all tests pass**

Run: `cd /Users/shenghuang/Desktop/Projects/job_applier && PYTHONPATH=src python -m pytest tests/ -v`
Expected: All tests pass (28+ tests)

- [ ] **Step 4: Commit**

```bash
git add src/job_applier/runner.py src/job_applier/__main__.py
git commit -m "feat: main runner orchestrator and CLI entry point"
```

- [ ] **Step 5: Final commit with all files**

```bash
git add -A
git status
git commit -m "feat: complete auto job applier implementation"
```

---

## Summary of All Files Created

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project config and dependencies |
| `src/job_applier/__init__.py` | Package init |
| `src/job_applier/__main__.py` | CLI entry point |
| `src/job_applier/config.py` | Config loading and validation |
| `src/job_applier/browser.py` | Camoufox REST API client |
| `src/job_applier/llm.py` | LLM provider abstraction |
| `src/job_applier/prompt.py` | Prompt building and response parsing |
| `src/job_applier/search.py` | Indeed job search engine |
| `src/job_applier/application.py` | AI-first application engine |
| `src/job_applier/accounts.py` | Account manager (SQLite) |
| `src/job_applier/notifications.py` | Desktop notifications and logging |
| `src/job_applier/runner.py` | Main orchestrator |
| `config.yaml` | Example config |
| `profile.yaml` | Example profile |
| `tests/test_config.py` | Config tests |
| `tests/test_browser.py` | Browser client tests |
| `tests/test_llm.py` | LLM provider tests |
| `tests/test_prompt.py` | Prompt building tests |
| `tests/test_search.py` | Search engine tests |
| `tests/test_application.py` | Application engine tests |
| `tests/test_accounts.py` | Account manager tests |
| `tests/test_notifications.py` | Notification tests |
