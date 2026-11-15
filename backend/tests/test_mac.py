import pytest
from sqlalchemy import select
from backend.models import Track, User
from backend.main import app
from backend import main


@pytest.fixture
def media(db_factory, tmp_path, monkeypatch):
    monkeypatch.setattr(main, "MEDIA_DIR", tmp_path)
    data = b"RIFF" + bytes(range(128))
    for level in (1, 2, 3):
        (tmp_path / f"{level}.wav").write_bytes(data)
    with db_factory() as db:
        db.add_all([Track(title=f"Track {level}", artist="Demo", security_level=level,
                          file_path=f"{level}.wav", duration=24) for level in (1, 2, 3)])
        db.commit()
    return data


@pytest.mark.parametrize("clearance,resource", [(a, b) for a in (1, 2, 3) for b in (1, 2, 3)])
def test_mac_matrix_and_range(client, db_factory, media, clearance, resource):
    account = {"login": "listener", "password": "Strong123!"}
    client.post("/api/register", json=account)
    client.post("/api/login", json=account)
    with db_factory() as db:
        db.scalar(select(User)).clearance_level = clearance
        db.commit()
    response = client.get(f"/api/tracks/{resource}/stream", headers={"Range": "bytes=0-9"})
    if clearance >= resource:
        assert response.status_code == 206
        assert response.content == media[:10]
        assert response.headers["content-range"] == f"bytes 0-9/{len(media)}"
        assert response.headers["content-type"] == "audio/wav"
    else:
        assert response.status_code == 403
        assert b"RIFF" not in response.content
    assert response.headers["cache-control"] == "no-store"
    assert len(client.get("/api/me/tracks").json()) == clearance


def test_anonymous_stream_and_static_bypass(client, media):
    for level in (1, 2, 3):
        assert client.get(f"/api/tracks/{level}/stream").status_code == 401
    assert client.get("/media/1.wav").status_code == 404
    assert client.get("/api/me/tracks").status_code == 401


def test_full_stream_range_errors_and_label_change(client, db_factory, media):
    account = {"login": "listener", "password": "Strong123!"}
    client.post("/api/register", json=account)
    client.post("/api/login", json=account)
    assert client.get("/api/tracks/1/stream").content == media
    assert client.get("/api/tracks/1/stream", headers={"Range": "bytes=99999-"}).status_code == 416
    assert client.get("/api/tracks/999/stream").status_code == 404
    with db_factory() as db:
        db.get(Track, 1).security_level = 3
        db.commit()
    assert client.get("/api/tracks/1/stream").status_code == 403


def test_media_path_containment(client, db_factory, media, tmp_path):
    account = {"login": "listener", "password": "Strong123!"}
    client.post("/api/register", json=account)
    client.post("/api/login", json=account)
    with db_factory() as db:
        db.get(Track, 1).file_path = "../private.txt"
        db.commit()
    assert client.get("/api/tracks/1/stream").status_code == 404
