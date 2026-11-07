"""Database connection for the dashboard. Credentials come from the Sql.env (or .env) file,
never from the code."""
import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from utils import decimals_to_float


def _load_env():
    """Look for Sql.env or .env in this folder and in the project folder above it."""
    here = Path(__file__).resolve().parent
    for folder in (here, here.parent):
        for name in ("Sql.env", ".env"):
            candidate = folder / name
            if candidate.exists():
                load_dotenv(candidate, override=True)
                return candidate
    return None


@st.cache_resource
def get_engine():
    _load_env()
    url = URL.create(
        "mysql+pymysql",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME"),
    )
    return create_engine(url, pool_pre_ping=True)


@st.cache_data(ttl=600, show_spinner=False)
def run_query(sql, params=None):
    """Run a SQL query and return a DataFrame. Only the parameters that the query uses are sent."""
    params = params or {}
    used = {k: v for k, v in params.items() if f":{k}" in sql}
    with get_engine().connect() as conn:
        df = pd.read_sql(text(sql), conn, params=used)
    return decimals_to_float(df)
