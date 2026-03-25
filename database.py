"""
database.py  –  MySQL connection & helpers for Bank of Bharat
"""
import mysql.connector
from mysql.connector import Error
import streamlit as st

# ── Update these if your MySQL config differs ──────────────────────────────
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",          # ← change to your MySQL root/user password
    "database": "bank_of_bharat",
    "charset": "utf8mb4",
    "autocommit": False,
    "connection_timeout": 10,
}
# ──────────────────────────────────────────────────────────────────────────


def get_connection():
    """Return a fresh MySQL connection; None on failure."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        st.error(f"Database connection error: {e}")
        return None


def fetchall(query: str, params: tuple = ()) -> list[dict]:
    """Execute a SELECT and return all rows as list-of-dicts."""
    conn = get_connection()
    if conn is None:
        return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(query, params)
        rows = cur.fetchall()
        return rows
    except Error as e:
        st.error(f"Query error: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def fetchone(query: str, params: tuple = ()) -> dict | None:
    """Execute a SELECT and return the first row as dict."""
    rows = fetchall(query, params)
    return rows[0] if rows else None


def execute(query: str, params: tuple = ()) -> int | None:
    """Execute INSERT / UPDATE / DELETE; return lastrowid or 0."""
    conn = get_connection()
    if conn is None:
        return None
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        return cur.lastrowid
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def execute_many(query: str, params_list: list[tuple]) -> bool:
    """Execute a batch INSERT/UPDATE."""
    conn = get_connection()
    if conn is None:
        return False
    try:
        cur = conn.cursor()
        cur.executemany(query, params_list)
        conn.commit()
        return True
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def execute_transaction(queries: list[tuple]) -> bool:
    """
    Execute multiple (query, params) tuples atomically.
    queries = [(sql1, params1), (sql2, params2), ...]
    """
    conn = get_connection()
    if conn is None:
        return False
    try:
        cur = conn.cursor()
        for query, params in queries:
            cur.execute(query, params)
        conn.commit()
        return True
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()
