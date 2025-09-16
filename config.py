# config.py
import os

try:
    import streamlit as st
    database_url = st.secrets.get("DATABASE_URL")
except Exception:
    database_url = None

if not database_url:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass
    database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise RuntimeError("DATABASE_URL not set")

# export
DATABASE_URL = database_url
