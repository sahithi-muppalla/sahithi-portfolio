import os, sqlite3
from pathlib import Path
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash

ROOT = Path(__file__).resolve().parent
(ROOT / "instance").mkdir(exist_ok=True)
DB = ROOT / "instance" / "portfolio.db"
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "local-demo-change-before-deploying")
ADMIN_USER = os.environ.get("ADMIN_USERNAME", "sahithi")
ADMIN_PASS = os.environ.get("ADMIN_PASSWORD", "ChangeMe123!")

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def setup():
    with conn() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS profile(id INTEGER PRIMARY KEY, name TEXT, headline TEXT, bio TEXT, email TEXT, github TEXT, linkedin TEXT);
        CREATE TABLE IF NOT EXISTS skills(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, level TEXT, category TEXT);
        CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, description TEXT, tech TEXT, link TEXT, featured INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS certificates(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, issuer TEXT, date TEXT, link TEXT);
        CREATE TABLE IF NOT EXISTS experience(id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, organization TEXT, period TEXT, description TEXT, link TEXT);
        """)
        if not db.execute("SELECT id FROM profile WHERE id=1").fetchone():
            db.execute("INSERT INTO profile VALUES(1,?,?,?,?,?,?)", (
                "Sahithi Muppalla", "Aspiring AI & Machine Learning Engineer",
                "I am an AIML student who enjoys problem solving, building projects, and exploring how technology can solve real-world problems.",
                "", "https://github.com/", "https://linkedin.com/"))
        if db.execute("SELECT COUNT(*) FROM skills").fetchone()[0] == 0:
            db.executemany("INSERT INTO skills(name,level,category) VALUES(?,?,?)", [
                ("C Programming","Proficient","Programming"),("Python","Learning","Programming"),
                ("Java & OOP","Learning","Programming"),("HTML & CSS","Learning","Web Development"),
                ("Problem Solving","Developing","Core Skills")])
        if db.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0:
            db.executemany("INSERT INTO projects(title,description,tech,link,featured) VALUES(?,?,?,?,?)", [
                ("Student Record System","A C project demonstrating student records and dynamic memory allocation.","C, calloc","",1),
                ("Python Password Authentication","A beginner-friendly authentication project using Python fundamentals.","Python","",0),
                ("Rock Paper Scissors","A command-line game with random choices and best-of-rounds gameplay.","Python","",0)])
        if db.execute("SELECT COUNT(*) FROM certificates").fetchone()[0] == 0:
            db.executemany("INSERT INTO certificates(title,issuer,date,link) VALUES(?,?,?,?)", [
                ("AI Fundamentals","IBM SkillsBuild","2026",""),("Web Development Fundamentals","IBM SkillsBuild","2026",""),
                ("Prompt Engineering for Everyone","Cognitive Class","2026","")])
setup()

def required(fn):
    @wraps(fn)
    def inner(*a, **kw):
        if not session.get("admin"): return redirect(url_for("login"))
        return fn(*a, **kw)
    return inner

@app.route("/")
def home():
    with conn() as db:
        p=db.execute("SELECT * FROM profile WHERE id=1").fetchone()
        skills=db.execute("SELECT * FROM skills ORDER BY category,name").fetchall()
        projects=db.execute("SELECT * FROM projects ORDER BY featured DESC,id DESC").fetchall()
        certs=db.execute("SELECT * FROM certificates ORDER BY id DESC").fetchall()
        experience=db.execute("SELECT * FROM experience ORDER BY id DESC").fetchall()
    return render_template("index.html", p=p, skills=skills, projects=projects, certs=certs, experience=experience)

@app.route("/admin/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=request.form.get("username",""); pw=request.form.get("password","")
        if u==ADMIN_USER and check_password_hash(generate_password_hash(ADMIN_PASS), pw):
            session["admin"]=True
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
        p=db.execute("SELECT * FROM profile WHERE id=1").fetchone()
        skills=db.execute("SELECT * FROM skills ORDER BY id DESC").fetchall()
        projects=db.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
        certs=db.execute("SELECT * FROM certificates ORDER BY id DESC").fetchall()
        experience=db.execute("SELECT * FROM experience ORDER BY id DESC").fetchall()
    return render_template("admin.html",p=p,skills=skills,projects=projects,certs=certs,experience=experience)

@app.route("/admin/profile",methods=["POST"])
@required
def profile_save():
    vals=[request.form.get(k,"").strip() for k in ("name","headline","bio","email","github","linkedin")]
    if not vals[0] or not vals[1] or not vals[2]:
        flash("Name, headline, and bio are required.","error")
    else:
        with conn() as db:
            db.execute("UPDATE profile SET name=?,headline=?,bio=?,email=?,github=?,linkedin=? WHERE id=1",vals)
        flash("Profile saved.","success")
    return redirect(url_for("admin"))

@app.route("/admin/add/<kind>",methods=["POST"])
@required
def add(kind):
    with conn() as db:
        if kind=="skills":
            name=request.form.get("name","").strip()
            if name: db.execute("INSERT INTO skills(name,level,category) VALUES(?,?,?)",(name,request.form.get("level","Learning"),request.form.get("category","Technical")))
        elif kind=="projects":
            title=request.form.get("title","").strip(); desc=request.form.get("description","").strip()
            if title and desc: db.execute("INSERT INTO projects(title,description,tech,link,featured) VALUES(?,?,?,?,?)",(title,desc,request.form.get("tech",""),request.form.get("link",""),1 if request.form.get("featured") else 0))
            else: flash("Project title and description are required.","error"); return redirect(url_for("admin"))
        elif kind=="certificates":
            title=request.form.get("title","").strip()
            if title: db.execute("INSERT INTO certificates(title,issuer,date,link) VALUES(?,?,?,?)",(title,request.form.get("issuer",""),request.form.get("date",""),request.form.get("link","")))
        elif kind=="experience":
            role=request.form.get("role","").strip(); organization=request.form.get("organization","").strip()
            if role and organization: db.execute("INSERT INTO experience(role,organization,period,description,link) VALUES(?,?,?,?,?)",(role,organization,request.form.get("period",""),request.form.get("description",""),request.form.get("link","")))
            else: flash("Role and organization are required.","error"); return redirect(url_for("admin"))
        else: return "Not found",404
    flash(kind.capitalize()+" saved.","success")
    return redirect(url_for("admin"))

@app.route("/admin/delete/<kind>/<int:item_id>",methods=["POST"])
@required
def delete(kind,item_id):
    tables={"skills":"skills","projects":"projects","certificates":"certificates","experience":"experience"}
    if kind not in tables: return "Not found",404
    with conn() as db: db.execute("DELETE FROM "+tables[kind]+" WHERE id=?",(item_id,))
    flash("Item deleted.","success")
    return redirect(url_for("admin"))

if __name__=="__main__":
    app.run(debug=True)
