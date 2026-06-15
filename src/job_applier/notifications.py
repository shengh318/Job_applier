# src/job_applier/notifications.py
"""Desktop notifications and application logging."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any


class NotificationSystem:
    """Handles desktop notifications and JSONL application logging."""

    def __init__(self, log_file: str = "./logs/applications.jsonl", desktop_enabled: bool = True):
        self.log_file = log_file
        self.desktop_enabled = desktop_enabled
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)

    def notify(self, title: str, message: str) -> None:
        """Send a desktop notification."""
        if not self.desktop_enabled:
            return
        try:
            import plyer.notification
            plyer.notification.notify(
                title=title,
                message=message,
                app_name="Job Applier",
            )
        except Exception:
            pass

    def log_application(
        self,
        job_title: str,
        company: str,
        status: str,
        url: str = "",
        account_created: bool = False,
        account_domain: str = "",
        account_email: str = "",
    ) -> None:
        """Log an application event to the JSONL file."""
        entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "job_title": job_title,
            "company": company,
            "status": status,
            "url": url,
        }
        if account_created:
            entry["account_created"] = True
            entry["account_domain"] = account_domain
            entry["account_email"] = account_email

        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

        self.notify(
            f"Applied: {job_title}",
            f"{company} — {status}",
        )
