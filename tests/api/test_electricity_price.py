import pytest
import pytest_asyncio
from jsonschema import validate
from starlette.testclient import TestClient

from boaviztapi.main import app
from tests.json_schemas.electricity import available_countries_schema

pytest_plugins = ('pytest_asyncio',)

@pytest_asyncio.fixture(scope="module")
def client():
    with TestClient(app) as client:
        yield client


@pytest.mark.asyncio
async def test_available_countries(client):
    res = client.get('/v1/electricity/available_countries')
    assert res.status_code == 200
    assert res.json()
    validate(res.json(), available_countries_schema)
