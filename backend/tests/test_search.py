import pytest
from backend.models import Track


@pytest.fixture
def catalog(db_factory):
    with db_factory() as db:
        db.add_all([
            Track(title="Night Drive", artist="Electronic Waves", security_level=1, file_path="public.wav", duration=24),
            Track(title="Deep Ocean", artist="Ambient Project", security_level=2, file_path="confidential.wav", duration=24),
            Track(title="Secret Sessions", artist="Studio X", security_level=3, file_path="secret.wav", duration=24)])
        db.commit()


def test_search_filters_and_detail(client, catalog):
    assert len(client.get("/api/tracks").json()) == 3
    for params in ({"q": "night"}, {"q": "Electronic"}, {"title": "Night", "artist": "Electronic"}):
        result = client.get("/api/tracks/search", params=params)
        assert result.status_code == 200
        assert [track["title"] for track in result.json()] == ["Night Drive"]
        assert "file_path" not in result.text
    assert client.get("/api/tracks", params={"title": "Night", "artist": "Studio"}).json() == []
    assert client.get("/api/tracks", params={"q": "%"}).json() == []
    assert client.get("/api/tracks", params={"q": "' OR 1=1 --"}).json() == []
    assert client.get("/api/tracks", params={"q": "x" * 101}).status_code == 422
    assert client.get("/api/tracks/1").json()["title"] == "Night Drive"
    assert client.get("/api/tracks/999").status_code == 404
