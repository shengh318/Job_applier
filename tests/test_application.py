# tests/test_application.py
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from job_applier.application import ApplicationEngine


@pytest.fixture
def browser():
    return MagicMock()


@pytest.fixture
def llm():
    return MagicMock()


@pytest.fixture
def accounts():
    return MagicMock()


@pytest.fixture
def notifications():
    return MagicMock()


@pytest.fixture
def engine(browser, llm, accounts, notifications):
    return ApplicationEngine(
        browser=browser,
        llm=llm,
        accounts=accounts,
        notifications=notifications,
        profile={"name": "John", "email": "john@example.com"},
        resume_path="/path/to/resume.pdf",
    )


@pytest.mark.asyncio
async def test_fill_fields(engine):
    engine.browser.fill = AsyncMock(return_value={"status": "filled"})

    fields = [
        {"selector": "textbox 'First Name'", "value": "John"},
        {"selector": "textbox 'Email'", "value": "john@example.com"},
    ]
    await engine._fill_fields("tab123", fields)
    assert engine.browser.fill.call_count == 2


@pytest.mark.asyncio
async def test_click_button(engine):
    engine.browser.click = AsyncMock(return_value={"status": "clicked"})
    await engine._click_button("tab123", "button 'Submit'")
    engine.browser.click.assert_called_once_with("tab123", "button 'Submit'")


@pytest.mark.asyncio
async def test_upload_resume(engine):
    engine.browser.upload_file = AsyncMock(return_value={"status": "uploaded"})
    fields = [{"selector": "upload 'Resume'", "action": "upload_file", "path": "/path/to/resume.pdf"}]
    await engine._fill_fields("tab123", fields)
    engine.browser.upload_file.assert_called_once_with("tab123", "upload 'Resume'", "/path/to/resume.pdf")


@pytest.mark.asyncio
async def test_detect_account_creation(engine):
    assert engine._detect_account_creation("workday.com", "Sign up for Workday") is True
    assert engine._detect_account_creation("indeed.com", "Apply now") is False
    assert engine._detect_account_creation("greenhouse.io", "Create account") is True


@pytest.mark.asyncio
async def test_handle_account_creation(engine):
    engine.browser.get_snapshot = AsyncMock(return_value="textbox 'Email'\nbutton 'Create Account'")
    engine.browser.fill = AsyncMock(return_value={"status": "filled"})
    engine.browser.click = AsyncMock(return_value={"status": "clicked"})
    engine.browser.get_url = AsyncMock(return_value="https://apply.workday.com/signup")
    engine.accounts.get.return_value = None
    engine.accounts.store = MagicMock()
    engine.llm.generate = AsyncMock(return_value=json.dumps({
        "fields": [
            {"selector": "textbox 'Email'", "value": "john+workday@example.com"},
            {"selector": "textbox 'Password'", "value": "Str0ngP@ss"},
        ],
        "click": "button 'Create Account'",
        "status": "account_created",
        "account": {"email": "john+workday@example.com", "password": "Str0ngP@ss"},
    }))

    result = await engine._handle_account_creation("tab123", "workday.com")
    assert result is True
    engine.accounts.store.assert_called_once()
