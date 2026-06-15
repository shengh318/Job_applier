# tests/test_accounts.py
import os
import tempfile
import pytest
from job_applier.accounts import AccountManager


@pytest.fixture
def manager(tmp_path):
    db_path = str(tmp_path / "test_accounts.db")
    return AccountManager(db_path=db_path)


def test_store_and_get(manager):
    manager.store("workday.com", "user@workday.com", "pass123")
    creds = manager.get("workday.com")
    assert creds is not None
    assert creds["email"] == "user@workday.com"
    assert creds["password"] == "pass123"


def test_get_nonexistent(manager):
    creds = manager.get("nonexistent.com")
    assert creds is None


def test_store_overwrites(manager):
    manager.store("workday.com", "old@workday.com", "oldpass")
    manager.store("workday.com", "new@workday.com", "newpass")
    creds = manager.get("workday.com")
    assert creds["email"] == "new@workday.com"


def test_list_accounts(manager):
    manager.store("workday.com", "a@b.com", "p1")
    manager.store("greenhouse.io", "a@c.com", "p2")
    accounts = manager.list_accounts()
    assert len(accounts) == 2
    domains = [a["domain"] for a in accounts]
    assert "workday.com" in domains
    assert "greenhouse.io" in domains


def test_delete_account(manager):
    manager.store("workday.com", "a@b.com", "p1")
    manager.delete("workday.com")
    assert manager.get("workday.com") is None
