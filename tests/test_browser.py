# tests/test_browser.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from job_applier.browser import CamoufoxClient


@pytest.fixture
def client():
    return CamoufoxClient(base_url="http://localhost:3000")


def test_client_init():
    client = CamoufoxClient(base_url="http://localhost:3000")
    assert client.base_url == "http://localhost:3000"


@pytest.mark.asyncio
async def test_create_tab(client):
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"tabId": "abc123", "url": "about:blank"}

    with patch.object(client, "_request", new_callable=AsyncMock, return_value=mock_response):
        tab = await client.create_tab("https://example.com")
        assert tab["tabId"] == "abc123"


@pytest.mark.asyncio
async def test_close_tab(client):
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch.object(client, "_request", new_callable=AsyncMock, return_value=mock_response):
        result = await client.close_tab("abc123")
        assert result is True


@pytest.mark.asyncio
async def test_click_element(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "clicked"}

    with patch.object(client, "_request", new_callable=AsyncMock, return_value=mock_response):
        result = await client.click("abc123", "button 'Submit'")
        assert result["status"] == "clicked"


@pytest.mark.asyncio
async def test_fill_field(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "filled"}

    with patch.object(client, "_request", new_callable=AsyncMock, return_value=mock_response):
        result = await client.fill("abc123", "textbox 'First Name'", "John")
        assert result["status"] == "filled"


@pytest.mark.asyncio
async def test_get_snapshot(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "snapshot": "textbox 'First Name'\ntextbox 'Email'\nbutton 'Submit'"
    }

    with patch.object(client, "_request", new_callable=AsyncMock, return_value=mock_response):
        snapshot = await client.get_snapshot("abc123")
        assert "textbox 'First Name'" in snapshot


@pytest.mark.asyncio
async def test_navigate(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"url": "https://example.com"}

    with patch.object(client, "_request", new_callable=AsyncMock, return_value=mock_response):
        result = await client.navigate("abc123", "https://example.com")
        assert result["url"] == "https://example.com"


@pytest.mark.asyncio
async def test_upload_file(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "uploaded"}

    with patch.object(client, "_request", new_callable=AsyncMock, return_value=mock_response):
        result = await client.upload_file("abc123", "upload 'Resume'", "/path/to/resume.pdf")
        assert result["status"] == "uploaded"
