"""One-time local setup. Existing .env is never overwritten."""
from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
target = root / ".env"
if target.exists():
    raise SystemExit(".env already exists; leaving it unchanged")
content = (root / ".env.example").read_text(encoding="utf-8")
for key in ("POSTGRES_PASSWORD", "SECRET_KEY", "DEMO_PUBLIC_PASSWORD", "DEMO_CONFIDENTIAL_PASSWORD", "DEMO_SECRET_PASSWORD"):
    content = content.replace(f"{key}=\n", f"{key}=Aa1!{secrets.token_hex(24)}\n")
with target.open("x", encoding="utf-8") as output:
    output.write(content)
try:
    target.chmod(0o600)
except OSError:
    pass
print("Created .env with random local credentials. Keep this file private.")
