import pytest


@pytest.mark.anyio
async def test_unknown_route_uses_error_envelope(client):
    response = await client.get("/api/v1/nope")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["request_id"]
    assert response.headers["x-request-id"] == body["request_id"]


@pytest.mark.anyio
async def test_client_request_id_is_preserved(client):
    response = await client.get("/api/v1/health", headers={"X-Request-ID": "req-123"})
    assert response.headers["x-request-id"] == "req-123"
