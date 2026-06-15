# tests/test_search.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from job_applier.search import IndeedSearcher


@pytest.fixture
def browser():
    b = MagicMock()
    b.create_tab = AsyncMock(return_value={"tabId": "t1"})
    b.close_tab = AsyncMock()
    b.navigate = AsyncMock()
    b.get_snapshot = AsyncMock()
    b.click = AsyncMock()
    return b


@pytest.fixture
def searcher(browser):
    return IndeedSearcher(browser)


def test_init(searcher):
    assert searcher is not None


@pytest.mark.asyncio
async def test_parse_job_listings():
    from job_applier.search import _parse_job_listings

    snapshot = """
link "Software Engineer at Acme Corp" [ref=e1]
text "San Francisco, CA"
text "$120,000 - $150,000 a year"
link "Apply now" [ref=e2]

link "Backend Developer at Beta Inc" [ref=e3]
text "Remote"
text "$100,000 - $130,000 a year"
link "Apply now" [ref=e4]
"""
    jobs = _parse_job_listings(snapshot)
    assert len(jobs) == 2
    assert jobs[0]["title"] == "Software Engineer at Acme Corp"
    assert jobs[0]["company"] == "Acme Corp"
    assert jobs[1]["title"] == "Backend Developer at Beta Inc"
    assert jobs[1]["company"] == "Beta Inc"


@pytest.mark.asyncio
async def test_search_returns_jobs(searcher):
    mock_snapshot = """
link "Software Engineer at Acme Corp" [ref=e1]
text "San Francisco, CA"
link "Apply now" [ref=e2]
"""
    with patch.object(searcher.browser, "get_snapshot", new_callable=AsyncMock, return_value=mock_snapshot):
        with patch.object(searcher.browser, "navigate", new_callable=AsyncMock):
            with patch.object(searcher.browser, "click", new_callable=AsyncMock):
                with patch.object(searcher.browser, "fill", new_callable=AsyncMock):
                    with patch("asyncio.sleep", new_callable=AsyncMock):
                        jobs = await searcher.search("Software Engineer", "San Francisco")
                        assert len(jobs) >= 1
                        assert jobs[0]["title"] == "Software Engineer at Acme Corp"

