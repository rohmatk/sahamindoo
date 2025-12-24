# 🎈 Blank app template

A simple Streamlit app template for you to modify!

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://blank-app-template.streamlit.app/)

### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```
   $ streamlit run streamlit_app.py
   ```

## 🔐 Secrets / Database (local dev)

This app expects SingleStore (MySQL) credentials to be available via Streamlit secrets or environment variables. If no credentials are found, the app will fall back to a local SQLite DB for development.

Create a file at `.streamlit/secrets.toml` with these keys (do NOT commit this file to source control):

```toml
SINGLESTORE_USER = "<your-user>"
SINGLESTORE_PASSWORD = "<your-password>"
SINGLESTORE_HOST = "<host-or-host:port>"
SINGLESTORE_DB = "<database>"
```

Alternatively, set environment variables: `SINGLESTORE_USER`, `SINGLESTORE_PASSWORD`, `SINGLESTORE_HOST`, `SINGLESTORE_DB`.

Add `.streamlit/` to your `.gitignore` to avoid accidentally committing secrets.
