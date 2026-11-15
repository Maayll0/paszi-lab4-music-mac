import os
import subprocess
import sys


def main():
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    from backend.seed import seed
    seed(demo_users=os.getenv("SEED_DEMO_USERS", "false").lower() == "true")
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")),
                access_log=False)


if __name__ == "__main__":
    main()
