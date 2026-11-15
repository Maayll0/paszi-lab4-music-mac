"""Mandatory read policy. Labels come exclusively from persisted server data."""
from fastapi import HTTPException
from backend.models import Track, User


def require_read_access(user: User, resource: Track):
    if user.clearance_level < resource.security_level:
        raise HTTPException(403, "Недостаточный уровень допуска")
