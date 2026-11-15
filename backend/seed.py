"""Idempotent demo catalogue and original synthesized audio (no external recordings)."""
import argparse
from array import array
import math
import os
from pathlib import Path
import sys
import wave

from sqlalchemy import select
from backend.database import SessionLocal
from backend.models import SecurityLevel, Track, User
from backend.schemas import RegisterRequest
from backend.security import hash_password

MEDIA_DIR = Path(os.getenv("MEDIA_DIR", "backend/media"))
DEMO_TRACKS = [
    ("Night Drive", "Electronic Waves", 1, "night-drive.wav", (220, 261.63, 329.63, 293.66)),
    ("Deep Ocean", "Ambient Project", 2, "deep-ocean.wav", (130.81, 164.81, 196, 146.83)),
    ("Secret Sessions", "Studio X", 3, "secret-sessions.wav", (261.63, 329.63, 392, 440)),
]


def synthesize(path: Path, notes: tuple, duration: int = 24):
    rate = 22050
    samples = array("h")
    for i in range(rate * duration):
        t = i / rate
        note = notes[int(t * 2) % len(notes)]
        envelope = min(1, t * 4, (duration - t) * 4)
        pulse = math.exp(-3 * (t % 0.5))
        tone = (math.sin(2 * math.pi * note * t) * pulse
                + 0.25 * math.sin(2 * math.pi * note / 2 * t)
                + 0.1 * math.sin(2 * math.pi * note * 2 * t))
        samples.append(int(11000 * envelope * tone))
    if sys.byteorder != "little":
        samples.byteswap()
    with wave.open(str(path), "wb") as output:
        output.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        output.writeframes(samples.tobytes())


def seed(demo_users: bool = False):
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    with SessionLocal() as db:
        for title, artist, level, filename, notes in DEMO_TRACKS:
            path = MEDIA_DIR / filename
            if not path.exists():
                synthesize(path, notes)
            if db.scalar(select(Track).where(Track.file_path == filename)) is None:
                db.add(Track(title=title, artist=artist, security_level=level, file_path=filename, duration=24))
        if demo_users:
            for level in SecurityLevel:
                login = f"demo_{level.name.lower()}"
                existing = db.scalar(select(User).where(User.login == login))
                if existing:
                    if existing.clearance_level != level:
                        raise ValueError(f"Existing {login} has a different clearance; refusing to elevate it")
                    continue
                password = os.getenv(f"DEMO_{level.name}_PASSWORD")
                if not password:
                    raise ValueError(f"Set DEMO_{level.name}_PASSWORD before creating demo accounts")
                RegisterRequest(login=login, password=password)
                db.add(User(login=login, password_hash=hash_password(password),
                            clearance_level=level, is_music_account=True))
        db.commit()
    print("Demo catalogue ready" + ("; demo accounts ready" if demo_users else ""))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo-users", action="store_true")
    seed(parser.parse_args().demo_users)
