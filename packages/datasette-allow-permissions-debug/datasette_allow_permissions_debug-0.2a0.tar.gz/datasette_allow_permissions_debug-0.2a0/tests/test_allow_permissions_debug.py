from datasette.app import Datasette
import pytest


@pytest.mark.asyncio
async def test_allows_access():
    ds = Datasette()
    response = await ds.client.get("/-/permissions")
    assert response.status_code == 200
