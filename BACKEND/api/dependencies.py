from services.session_store import store, SessionStore


def get_session_store() -> SessionStore:
    return store