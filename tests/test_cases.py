"""Smoke tests for the case endpoints. Full behavior tests added in Step 9."""


def test_list_cases_requires_api_key(client):
    resp = client.get("/api/cases")
    assert resp.status_code == 401
    assert resp.json()["detail"]["error"] == "UNAUTHORIZED"


def test_get_case_requires_api_key(client):
    resp = client.get("/api/cases/500000000000000AAA")
    assert resp.status_code == 401


def test_list_cases_passes_auth(client, auth_headers):
    # With a valid key, auth passes and we reach the (not-yet-implemented) Step 9.3 body.
    resp = client.get("/api/cases", headers=auth_headers)
    assert resp.status_code != 401
