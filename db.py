# db.py
import streamlit as st
from sqlalchemy import create_engine

def get_engine():
    return create_engine(
        f"mysql+pymysql://{st.secrets['SINGLESTORE_USER']}:{st.secrets['SINGLESTORE_PASSWORD']}@{st.secrets['SINGLESTORE_HOST']}/{st.secrets['SINGLESTORE_DB']}"
    )
