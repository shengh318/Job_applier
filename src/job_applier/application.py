# src/job_applier/application.py
"""AI-first application engine for filling job forms."""
from __future__ import annotations

import asyncio
import json
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
        if isinstance(response, str):
            response = json.loads(response)
        parsed = parse_llm_response(response)

        if parsed.get("status") == "account_created" and parsed.get("account"):
            await self._fill_fields(tab_id, parsed["fields"])
            if parsed.get("click"):
                await self._click_button(tab_id, parsed["click"])
            account = parsed["account"]
            self.accounts.store(domain, account["email"], account["password"])
            self.notifications.notify(
                f"Account created on {domain}",
                f"Email: {account['email']}\nPassword: {account['password']}",
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
                if isinstance(response, str):
                    response = json.loads(response)
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
