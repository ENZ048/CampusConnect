def test_metrics_endpoint_returns_prometheus_format(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.text
    assert "# HELP" in body
    assert "# TYPE" in body
    assert "http_requests_total" in body or "python_info" in body
