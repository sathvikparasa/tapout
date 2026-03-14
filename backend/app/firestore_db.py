"""
Firestore database client.
Wraps firebase_admin.firestore_async to provide a singleton async client.
Firebase app must be initialized (via firebase_admin.initialize_app) before calling get_db().
"""
from firebase_admin import firestore_async


def get_db():
    """Return the Firestore async client. Firebase app must already be initialized."""
    return firestore_async.client(database="warnabrotha")
