"""Ephemeral database/media for browser tests, never the user's application DB."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

with tempfile.TemporaryDirectory(prefix="musicaccess-e2e-") as temporary:
    os.environ["DATABASE_URL"] = "sqlite:///" + (Path(temporary) / "test.db").as_posix()
    os.environ["MEDIA_DIR"] = str(Path(temporary) / "media")
    os.environ["APP_ENV"] = "development"
    for level in ("PUBLIC", "CONFIDENTIAL", "SECRET"):
        os.environ[f"DEMO_{level}_PASSWORD"] = os.environ["MUSICACCESS_TEST_PASSWORD"]
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    from backend.seed import seed
    seed(demo_users=True)
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, log_level="warning")
