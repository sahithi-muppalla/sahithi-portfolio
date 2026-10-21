
import os
import sqlite3
from pathlib import Path
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash
)

ROOT = Path(__file__).resolve().parent
(ROOT / "instance").mkdir(exist_ok=True)

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
USE_POSTGRES = bool(DATABASE_URL)

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY", "local-demo-change-before-deploying"
)

ADMIN_USER = os.environ.get("ADMIN_USERNAME", "sahithi")
ADMIN_PASS = os.environ.get("ADMIN_PASSWORD", "ChangeMe123!")


class DatabaseConnection:
    """Support SQLite locally and PostgreSQL when DATABASE_URL is configured."""

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
            self.db = sqlite3.connect(
                ROOT / "instance" / "portfolio.db"
            )
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


def conn():
    return DatabaseConnection()


def setup():
    statements = [
        """CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY,
            name TEXT,
            headline TEXT,
            bio TEXT,
            email TEXT,
            github TEXT,
            linkedin TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS skills (
            id BIGSERIAL PRIMARY KEY,
            name TEXT,
            level TEXT,
            category TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS projects (
            id BIGSERIAL PRIMARY KEY,
            title TEXT,
            description TEXT,
            tech TEXT,
            link TEXT,
            featured INTEGER DEFAULT 0
        )""",
        """CREATE TABLE IF NOT EXISTS certificates (
            id BIGSERIAL PRIMARY KEY,
            title TEXT,
            issuer TEXT,
            date TEXT,
            link TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS experience (
            id BIGSERIAL PRIMARY KEY,
            role TEXT,
            organization TEXT,
            period TEXT,
            description TEXT,
            link TEXT
        )""",
    ]

    if not USE_POSTGRES:
        statements[1] = statements[1].replace(
            "BIGSERIAL PRIMARY KEY",
            "INTEGER PRIMARY KEY AUTOINCREMENT"
        )
        statements[2] = statements[2].replace(
            "BIGSERIAL PRIMARY KEY",
            "INTEGER PRIMARY KEY AUTOINCREMENT"
        )
        statements[3] = statements[3].replace(
            "BIGSERIAL PRIMARY KEY",
            "INTEGER PRIMARY KEY AUTOINCREMENT"
        )
        statements[4] = statements[4].replace(
            "BIGSERIAL PRIMARY KEY",
            "INTEGER PRIMARY KEY AUTOINCREMENT"
        )

    with conn() as db:
        for statement in statements:
            db.execute(statement)

        # Create the default profile only if it doesn't exist.
        db.execute(
            """INSERT INTO profile
               (id, name, headline, bio, email, github, linkedin)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT (id) DO NOTHING""",
            (
                1,
                "Sahithi Muppalla",
                "Aspiring AI & Machine Learning Engineer",
                "I am an AIML student who enjoys problem solving, "
                "building projects, and exploring how technology "
                "can solve real-world problems.",
                "",
                "https://github.com/",
                "https://linkedin.com/",
            ),
        )

        count = db.execute(
            "SELECT COUNT(*) AS total FROM skills"
        ).fetchone()["total"]

        if count == 0:
            for item in [
                ("C Programming", "Proficient", "Programming"),
                ("Python", "Learning", "Programming"),
                ("Java & OOP", "Learning", "Programming"),
                ("HTML & CSS", "Learning", "Web Development"),
                ("Problem Solving", "Developing", "Core Skills"),
            ]:
                db.execute(
                    "INSERT INTO skills (name, level, category) "
                    "VALUES (?, ?, ?)",
                    item,
                )

        count = db.execute(
            "SELECT COUNT(*) AS total FROM projects"
        ).fetchone()["total"]

        if count == 0:
            for item in [
                (
                    "Student Record System",
                    "A C project demonstrating student records "
                    "and dynamic memory allocation.",
                    "C, calloc",
                    "",
                    1,
                ),
                (
                    "Python Password Authentication",
                    "A beginner-friendly authentication project "
                    "using Python fundamentals.",
                    "Python",
                    "",
                    0,
                ),
                (
                    "Rock Paper Scissors",
                    "A command-line game with random choices "
                    "and best-of-rounds gameplay.",
                    "Python",
                    "",
                    0,
                ),
            ]:
                db.execute(
                    "INSERT INTO projects "
                    "(title, description, tech, link, featured) "
                    "VALUES (?, ?, ?, ?, ?)",
                    item,
                )

        count = db.execute(
            "SELECT COUNT(*) AS total FROM certificates"
        ).fetchone()["total"]

        if count == 0:
            for item in [
                ("AI Fundamentals", "IBM SkillsBuild", "2026", ""),
                (
                    "Web Development Fundamentals",
                    "IBM SkillsBuild",
                    "2026",
                    "",
                ),
                (
                    "Prompt Engineering for Everyone",
                    "Cognitive Class",
                    "2026",
                    "",
                ),
            ]:
                db.execute(
                    "INSERT INTO certificates (title, issuer, date, link) "
                    "VALUES (?, ?, ?, ?)",
                    item,
                )


setup()


def required(fn):
    @wraps(fn)
    def inner(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return inner


@app.route("/")
def home():
    with conn() as db:
        p = db.execute(
            "SELECT * FROM profile WHERE id = 1"
        ).fetchone()
        skills = db.execute(
            "SELECT * FROM skills ORDER BY category, name"
        ).fetchall()
        projects = db.execute(
            "SELECT * FROM projects ORDER BY featured DESC, id DESC"
        ).fetchall()
        certs = db.execute(
            "SELECT * FROM certificates ORDER BY id DESC"
        ).fetchall()
        experience = db.execute(
            "SELECT * FROM experience ORDER BY id DESC"
        ).fetchall()

    return render_template(
        "index.html",
        p=p,
        skills=skills,
        projects=projects,
        certs=certs,
        experience=experience,
    )


@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == ADMIN_USER and password == ADMIN_PASS:
            session["admin"] = True
            return redirect(url_for("admin"))

        flash("Incorrect username or password.", "error")

    return render_template("login.html")


@app.route("/admin/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/admin")
@required
def admin():
    with conn() as db:
        p = db.execute(
            "SELECT * FROM profile WHERE id = 1"
        ).fetchone()
        skills = db.execute(
            "SELECT * FROM skills ORDER BY id DESC"
        ).fetchall()
        projects = db.execute(
            "SELECT * FROM projects ORDER BY id DESC"
        ).fetchall()
        certs = db.execute(
            "SELECT * FROM certificates ORDER BY id DESC"
        ).fetchall()
        experience = db.execute(
            "SELECT * FROM experience ORDER BY id DESC"
        ).fetchall()

    return render_template(
        "admin.html",
        p=p,
        skills=skills,
        projects=projects,
        certs=certs,
        experience=experience,
    )


@app.route("/admin/profile", methods=["POST"])
@required
def profile_save():
    values = [
        request.form.get(key, "").strip()
        for key in (
            "name", "headline", "bio",
            "email", "github", "linkedin"
        )
    ]

    if not values[0] or not values[1] or not values[2]:
        flash("Name, headline, and bio are required.", "error")
    else:
        with conn() as db:
            db.execute(
                """UPDATE profile
                   SET name = ?, headline = ?, bio = ?,
                       email = ?, github = ?, linkedin = ?
                   WHERE id = 1""",
                values,
            )
        flash("Profile saved.", "success")

    return redirect(url_for("admin"))


@app.route("/admin/add/<kind>", methods=["POST"])
@required
def add(kind):
    with conn() as db:
        if kind == "skills":
            name = request.form.get("name", "").strip()
            if not name:
                flash("Skill name is required.", "error")
                return redirect(url_for("admin"))

            db.execute(
                "INSERT INTO skills (name, level, category) "
                "VALUES (?, ?, ?)",
                (
                    name,
                    request.form.get("level", "Learning"),
                    request.form.get("category", "Technical"),
                ),
            )

        elif kind == "projects":
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()

            if not title or not description:
                flash(
                    "Project title and description are required.",
                    "error",
                )
                return redirect(url_for("admin"))

            db.execute(
                """INSERT INTO projects
                   (title, description, tech, link, featured)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    title,
                    description,
                    request.form.get("tech", ""),
                    request.form.get("link", ""),
                    1 if request.form.get("featured") else 0,
                ),
            )

        elif kind == "certificates":
            title = request.form.get("title", "").strip()
            if not title:
                flash("Certificate title is required.", "error")
                return redirect(url_for("admin"))

            db.execute(
                "INSERT INTO certificates (title, issuer, date, link) "
                "VALUES (?, ?, ?, ?)",
                (
                    title,
                    request.form.get("issuer", ""),
                    request.form.get("date", ""),
                    request.form.get("link", ""),
                ),
            )

        elif kind == "experience":
            role = request.form.get("role", "").strip()
            organization = request.form.get("organization", "").strip()

            if not role or not organization:
                flash(
                    "Role and organization are required.",
                    "error",
                )
                return redirect(url_for("admin"))

            db.execute(
                """INSERT INTO experience
                   (role, organization, period, description, link)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    role,
                    organization,
                    request.form.get("period", ""),
                    request.form.get("description", ""),
                    request.form.get("link", ""),
                ),
            )

        else:
            return "Not found", 404

    flash(kind.capitalize() + " saved.", "success")
    return redirect(url_for("admin"))


@app.route(
    "/admin/delete/<kind>/<int:item_id>",
    methods=["POST"],
)
@required
def delete(kind, item_id):
    allowed_tables = {
        "skills": "skills",
        "projects": "projects",
        "certificates": "certificates",
        "experience": "experience",
    }

    if kind not in allowed_tables:
        return "Not found", 404

    with conn() as db:
        db.execute(
            "DELETE FROM " + allowed_tables[kind] + " WHERE id = ?",
            (item_id,),
        )

    flash("Item deleted.", "success")
    return redirect(url_for("admin"))


if __name__ == "__main__":
    app.run(debug=True)
