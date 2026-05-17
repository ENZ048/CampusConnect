def test_request_id_header_is_present(client):
    response = client.get("/healthz")
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) >= 16


def test_inbound_request_id_is_propagated(client):
    response = client.get("/healthz", headers={"X-Request-ID": "abc-123"})
    assert response.headers["x-request-id"] == "abc-123"
