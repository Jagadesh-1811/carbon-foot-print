import firebase_admin
from firebase_admin import credentials, firestore
import os

_db = None


def init_firebase():
    global _db
    if not firebase_admin._apps:
        cred_path = os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS", "./carbon-foot-print-64d5f-firebase-adminsdk-fbsvc-d3a7f9e540.json"
        )
        if not os.path.isabs(cred_path):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.abspath(os.path.join(current_dir, ".."))
            resolved_path = os.path.join(backend_dir, os.path.basename(cred_path))
            if os.path.exists(resolved_path):
                cred_path = resolved_path
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    _db = firestore.client()
    print("[Firebase] Firestore initialized OK")


def get_db():
    """Return the Firestore client. Call init_firebase() first."""
    return _db
