# tests/test_prompt.py
import json
import pytest
from job_applier.prompt import (
    build_form_filling_prompt,
    build_account_creation_prompt,
    parse_llm_response,
)


def test_build_form_filling_prompt_contains_snapshot():
    prompt = build_form_filling_prompt(
        snapshot="textbox 'First Name'\nbutton 'Submit'",
        profile={"name": "John", "email": "john@example.com"},
        job_description="We are hiring a software engineer",
    )
    assert "textbox 'First Name'" in prompt
    assert "John" in prompt
    assert "software engineer" in prompt


def test_build_account_creation_prompt_contains_domain():
    prompt = build_account_creation_prompt(
        snapshot="textbox 'Email'\ntextbox 'Password'\nbutton 'Create Account'",
        profile={"name": "John", "email": "john@example.com"},
        domain="workday.com",
    )
    assert "workday.com" in prompt
    assert "textbox 'Email'" in prompt
    assert "Create Account" in prompt


def test_parse_llm_response_valid_json():
    response = {
        "fields": [
            {"selector": "textbox 'First Name'", "value": "John"},
        ],
        "click": "button 'Next'",
        "status": "continue",
    }
    parsed = parse_llm_response(response)
    assert len(parsed["fields"]) == 1
    assert parsed["click"] == "button 'Next'"
    assert parsed["status"] == "continue"


def test_parse_llm_response_missing_status():
    response = {"fields": [], "click": None}
    parsed = parse_llm_response(response)
    assert parsed["status"] == "unknown"


def test_parse_llm_response_account_status():
    response = {
        "fields": [{"selector": "textbox 'Email'", "value": "a@b.com"}],
        "click": "button 'Create Account'",
        "status": "account_created",
        "account": {"email": "a@b.com", "password": "pass123"},
    }
    parsed = parse_llm_response(response)
    assert parsed["status"] == "account_created"
    assert parsed["account"]["email"] == "a@b.com"
