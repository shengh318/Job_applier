# src/job_applier/browser.py
"""Camoufox REST API client for browser automation."""
from __future__ import annotations

import httpx


class CamoufoxClient:
    """Client for the Camoufox browser REST API."""

    def __init__(self, base_url: str = "http://localhost:3000", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._http = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        return await self._http.request(method, path, **kwargs)

    async def create_tab(self, url: str = "about:blank") -> dict:
        """Open a new browser tab."""
        resp = await self._request("POST", "/tabs", json={"url": url})
        resp.raise_for_status()
        return resp.json()

    async def close_tab(self, tab_id: str) -> bool:
        """Close a browser tab."""
        resp = await self._request("DELETE", f"/tabs/{tab_id}")
        resp.raise_for_status()
        return True

    async def navigate(self, tab_id: str, url: str) -> dict:
        """Navigate a tab to a URL."""
        resp = await self._request("POST", f"/tabs/{tab_id}/navigate", json={"url": url})
        resp.raise_for_status()
        return resp.json()

    async def get_snapshot(self, tab_id: str) -> str:
        """Get accessibility snapshot of the current page."""
        resp = await self._request("GET", f"/tabs/{tab_id}/snapshot")
        resp.raise_for_status()
        data = resp.json()
        return data.get("snapshot", "")

    async def click(self, tab_id: str, selector: str) -> dict:
        """Click an element by accessibility selector."""
        resp = await self._request("POST", f"/tabs/{tab_id}/click", json={"selector": selector})
        resp.raise_for_status()
        return resp.json()

    async def fill(self, tab_id: str, selector: str, value: str) -> dict:
        """Fill a form field with a value."""
        resp = await self._request("POST", f"/tabs/{tab_id}/fill", json={"selector": selector, "value": value})
        resp.raise_for_status()
        return resp.json()

    async def upload_file(self, tab_id: str, selector: str, file_path: str) -> dict:
        """Upload a file to a file input field."""
        resp = await self._request("POST", f"/tabs/{tab_id}/upload", json={"selector": selector, "path": file_path})
        resp.raise_for_status()
        return resp.json()

    async def select_option(self, tab_id: str, selector: str, value: str) -> dict:
        """Select an option from a dropdown."""
        resp = await self._request("POST", f"/tabs/{tab_id}/select", json={"selector": selector, "value": value})
        resp.raise_for_status()
        return resp.json()

    async def get_url(self, tab_id: str) -> str:
        """Get the current URL of a tab."""
        resp = await self._request("GET", f"/tabs/{tab_id}/url")
        resp.raise_for_status()
        return resp.json().get("url", "")

    async def get_title(self, tab_id: str) -> str:
        """Get the current page title."""
        resp = await self._request("GET", f"/tabs/{tab_id}/title")
        resp.raise_for_status()
        return resp.json().get("title", "")

    async def wait_for_navigation(self, tab_id: str, timeout: float = 10.0) -> str:
        """Wait for navigation to complete and return new URL."""
        resp = await self._request("POST", f"/tabs/{tab_id}/wait-navigation", json={"timeout": timeout})
        resp.raise_for_status()
        return resp.json().get("url", "")

    async def close(self):
        """Close the HTTP client."""
        await self._http.aclose()
