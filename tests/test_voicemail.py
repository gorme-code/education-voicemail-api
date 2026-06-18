"""Smoke tests for the voicemail endpoints. Full behavior tests added in Step 9."""


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_voicemail_requires_api_key(client):
    body = {
        "caller_phone": "8035551234",
        "caller_name": "Test Caller",
        "email_timestamp": "2026-06-18T10:30:00Z",
        "email_subject": "[EXTERNAL] Voice Message Attached from 8035551234 - Test Caller",
        "external_id": "voicemail-8035551234-2026-06-18T10:30:00Z",
    }
    resp = client.post("/api/voicemail", json=body)
    assert resp.status_code == 401
    assert resp.json()["detail"]["error"] == "UNAUTHORIZED"


def test_create_voicemail_rejects_wrong_key(client):
    resp = client.post("/api/voicemail", json={}, headers={"X-API-Key": "wrong"})
    assert resp.status_code == 401
