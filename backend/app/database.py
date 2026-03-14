"""
Legacy database module — replaced by app/firestore_db.py.
Kept as a shim to avoid import errors in tests.
"""
from app.firestore_db import get_db

__all__ = ["get_db"]
