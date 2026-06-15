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
                "title": full_title,
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
