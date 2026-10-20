import os
import sqlite3
from pathlib import Path
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash

ROOT = Path(__file__).resolve().parent
(ROOT / "instance").mkdir(exist_ok=True)

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
USE_POSTGRES = bool(DATABASE_URL)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "local-demo-change-before-deploying")
ADMIN_USER = os.environ.get("ADMIN_USERNAME", "sahithi")
ADMIN_PASS = os.environ.get("ADMIN_PASSWORD", "ChangeMe123!")


class DatabaseConnection:
    """Small adapter so the existing app can use SQLite locally or PostgreSQL on Render."""
    def __init__(self):
        self.is_postgres = USE_POSTGRES
        if self.is_postgres:
            import psycopg
            from psycopg.rows import dict_row

            url = DATABASE_URL
            if url.startswith("postgres://"):
                url = "postgresql://" + url[len("postgres://"):]
            self.db = psycopg.connect(url, row_factory=dict_row)
        else:
            self.db = sqlite3.connect(ROOT / "instance" / "portfolio.db")
            self.db.row_factory = sqlite3.Row

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if exc_type is None:
                self.db.commit()
            else:
                self.db.rollback()
        finally:
            self.db.close()
        return False

    def execute(self, sql, params=()):
        if self.is_postgres:
            sql = sql.replace("?", "%s")
        return self.db.execute(sql, params)

    def close(self):
        self.db.close()


def conn():
    return DatabaseConnection()


def setup():
    if USE_POSTGRES:
        statements = [
            """CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY, name TEXT, headline TEXT, bio TEXT,
                email TEXT, github TEXT, linkedin TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS skills (
                id BIGSERIAL PRIMARY KEY, name TEXT, level TEXT, category TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS projects (
                id BIGSERIAL PRIMARY KEY, title TEXT, description TEXT, tech TEXT,
                link TEXT, featured INTEGER DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS certificates (
                id BIGSERIAL PRIMARY KEY, title TEXT, issuer TEXT, date TEXT, link TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS experience (
                id BIGSERIAL PRIMARY KEY, role TEXT, organization TEXT, period TEXT,
                description TEXT, link TEXT
            )""",
        ]
    else:
        statements = [
            """CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY, name TEXT, headline TEXT, bio TEXT,
                email TEXT, github TEXT, linkedin TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, level TEXT, category TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, description TEXT, tech TEXT,
                link TEXT, featured INTEGER DEFAULT 0
            )""",