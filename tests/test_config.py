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
