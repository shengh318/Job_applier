# src/job_applier/prompt.py
"""Prompt building and response parsing for LLM interactions."""
from __future__ import annotations

import json
from typing import Any


def build_form_filling_prompt(snapshot: str, profile: dict[str, Any], job_description: str) -> str:
    """Build a prompt for the LLM to fill a form based on an accessibility snapshot."""
    profile_text = json.dumps(profile, indent=2)
    return f"""You are filling out a job application form. Given the accessibility snapshot of the page, your profile data, and the job description, determine what to fill in and what button to click.

## Page Accessibility Snapshot
{snapshot}

## Your Profile
{profile_text}

## Job Description
{job_description}

Respond with JSON only. Format:
{{
  "fields": [
    {{"selector": "accessibility selector", "value": "value to fill"}}
  ],
  "click": "accessibility selector of button to click" or null,
  "status": "continue" | "done" | "needs_user_input" | "error",
  "message": "optional message if needs_user_input or error"
}}

Rules:
- For "upload" fields, use: {{"selector": "...", "action": "upload_file", "path": "/path/to/resume.pdf"}}
- For radio buttons/checkboxes, set value to the label text
- For dropdowns, set value to the option text
- For "submit" or "apply" buttons, click them and set status to "done" if it's the last page
- If you see a review/confirmation page, click submit and set status to "done"
- If a field cannot be determined from profile, set status to "needs_user_input"
- If a page appears broken or unexpected, set status to "error"
- Use screening_answers from profile when available
"""


def build_account_creation_prompt(snapshot: str, profile: dict[str, Any], domain: str) -> str:
    """Build a prompt for creating an account on an external site."""
    profile_text = json.dumps(profile, indent=2)
    return f"""You are creating an account on {domain}. Given the accessibility snapshot and profile data, fill out the signup form.

## Page Accessibility Snapshot
{snapshot}

## Your Profile
{profile_text}

Respond with JSON only. Format:
{{
  "fields": [
    {{"selector": "accessibility selector", "value": "value to fill"}}
  ],
  "click": "accessibility selector of button to click" or null,
  "status": "account_created",
  "account": {{"email": "generated email", "password": "generated strong password"}}
}}

Rules:
- Use the email from profile with a +{domain} suffix (e.g., name+workday@example.com)
- Generate a strong random password (12+ chars, mixed case, numbers, symbols)
- Fill all required fields
- Click the create/signup/register button
- Always set status to "account_created"
"""


def parse_llm_response(response: str | dict[str, Any]) -> dict[str, Any]:
    """Parse and normalize LLM response into expected format."""
    if isinstance(response, str):
        response = json.loads(response)

    fields = response.get("fields", [])
    click = response.get("click")
    status = response.get("status", "unknown")
    message = response.get("message", "")
    account = response.get("account")

    result: dict[str, Any] = {
        "fields": fields,
        "click": click,
        "status": status,
        "message": message,
    }

    if account:
        result["account"] = account

    return result
