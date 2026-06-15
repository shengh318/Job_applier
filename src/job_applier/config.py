# src/job_applier/config.py
"""Configuration loading and validation."""
from __future__ import annotations

import os
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

    cfg = Config(
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

    # Resolve env:VAR references in api_key
    if cfg.llm.api_key.startswith("env:"):
        env_var = cfg.llm.api_key[4:]
        cfg.llm.api_key = os.environ.get(env_var, "")

    return cfg


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
