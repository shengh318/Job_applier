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
            desktop_enabled=self.config.notifications.desktop,
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
                )

                if result["status"] == "applied":
                    self.notifications.notify("Job Applier", f"Applied to {job['title']} at {job['company']}")
                    logger.info("Successfully applied to %s", job["title"])
                elif result["status"] == "needs_input":
                    self.notifications.notify(
                        "Job Applier",
                        f"Needs input for {job['title']}: {result.get('message', '')}",
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
