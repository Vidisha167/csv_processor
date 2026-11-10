from unittest.mock import MagicMock

from app import main, storage


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_upload_rejects_non_csv(client):
    r = client.post("/upload", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert r.status_code == 400


def test_upload_creates_pending_job_and_queues_it(client, monkeypatch):
    fake_upload = MagicMock()
    fake_delay = MagicMock()
    monkeypatch.setattr(storage, "upload_file", fake_upload)
    monkeypatch.setattr(main.process_csv, "delay", fake_delay)

    r = client.post("/upload", files={"file": ("data.csv", b"a,b\n1,2\n", "text/csv")})
    assert r.status_code == 202
    body = r.json()
    assert body["status"] == "pending"

    fake_upload.assert_called_once()
    fake_delay.assert_called_once_with(body["job_id"])

    # The job should now be readable through the status endpoint
    r = client.get(f"/jobs/{body['job_id']}")
    assert r.status_code == 200
    assert r.json()["status"] == "pending"


def test_unknown_job_returns_404(client):
    r = client.get("/jobs/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


def test_malformed_job_id_returns_422(client):
    r = client.get("/jobs/abc")
    assert r.status_code == 422