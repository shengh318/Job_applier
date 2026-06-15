# tests/test_notifications.py
import json
import os
import tempfile
import pytest

from job_applier.notifications import NotificationSystem


@pytest.fixture
def log_file(tmp_path):
    return str(tmp_path / "applications.jsonl")


@pytest.fixture
def system(log_file):
    return NotificationSystem(log_file=log_file, desktop_enabled=False)


def test_log_application(system, log_file):
    system.log_application(
        job_title="Software Engineer",
        company="Acme Corp",
        status="applied",
    )
    with open(log_file) as f:
        lines = f.readlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["job_title"] == "Software Engineer"
    assert entry["company"] == "Acme Corp"
    assert entry["status"] == "applied"


def test_log_account_created(system, log_file):
    system.log_application(
        job_title="Backend Engineer",
        company="TechCo",
        status="applied",
        account_created=True,
        account_domain="workday.com",
        account_email="user+workday@example.com",
    )
    with open(log_file) as f:
        entry = json.loads(f.readline())
    assert entry["account_created"] is True
    assert entry["account_domain"] == "workday.com"


def test_log_appends_multiple(system, log_file):
    system.log_application(job_title="Job 1", company="C1", status="applied")
    system.log_application(job_title="Job 2", company="C2", status="skipped")
    with open(log_file) as f:
        lines = f.readlines()
    assert len(lines) == 2


def test_notify_skipped_when_disabled():
    system = NotificationSystem(desktop_enabled=False)
    system.notify("Test Title", "Test Message")


def test_log_application_triggers_notify(monkeypatch, log_file):
    called_with = {}
    system = NotificationSystem(log_file=log_file, desktop_enabled=True)

    def fake_notify(title, message):
        called_with["title"] = title
        called_with["message"] = message

    monkeypatch.setattr(system, "notify", fake_notify)
    system.log_application(job_title="SE", company="Acme", status="applied")
    assert called_with["title"] == "Applied: SE"
