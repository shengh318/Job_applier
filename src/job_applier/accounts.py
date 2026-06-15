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
        cursor = self._conn.execute(
            "SELECT email, password FROM accounts WHERE domain = ?", (domain,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {"email": row["email"], "password": row["password"]}

    def list_accounts(self) -> list[dict[str, Any]]:
        """List all stored accounts."""
        cursor = self._conn.execute("SELECT domain, email FROM accounts")
        return [{"domain": row["domain"], "email": row["email"]} for row in cursor]

    def delete(self, domain: str) -> None:
        """Delete credentials for a domain."""
        self._conn.execute("DELETE FROM accounts WHERE domain = ?", (domain,))
        self._conn.commit()

    def close(self):
        self._conn.close()
