# db.py
import os
import streamlit as st
from streamlit.runtime.secrets import StreamlitSecretNotFoundError
from sqlalchemy import create_engine


def _get_secret(key: str):
    """Safely get a secret from Streamlit secrets, falling back to environment vars."""
    try:
        # Accessing st.secrets[...] will raise StreamlitSecretNotFoundError if no secrets file exists
        return st.secrets[key]
    except (KeyError, StreamlitSecretNotFoundError):
        return os.getenv(key)


def get_engine():
    """Return a SQLAlchemy engine.

    If SingleStore credentials are available in Streamlit secrets or environment variables,
    connect to SingleStore. Otherwise fall back to a local SQLite DB for local development.
    """
    user = _get_secret('SINGLESTORE_USER')
    password = _get_secret('SINGLESTORE_PASSWORD')
    host = _get_secret('SINGLESTORE_HOST')
    db = _get_secret('SINGLESTORE_DB')

    if all([user, password, host, db]):
        return create_engine(f"mysql+pymysql://{user}:{password}@{host}/{db}")

    # Fallback to local SQLite (safe for local dev)
    try:
        st.warning(
            "No SingleStore credentials found; using local SQLite fallback.\n"
            "Create a `.streamlit/secrets.toml` or set env vars: SINGLESTORE_USER, SINGLESTORE_PASSWORD, SINGLESTORE_HOST, SINGLESTORE_DB"
        )
    except Exception:
        # If Streamlit UI isn't available (e.g., during unit tests), ignore
        pass

    return create_engine('sqlite:///local_cache.db')
