# Sahithi Muppalla — Editable Portfolio

A responsive portfolio and admin dashboard made with Flask, SQLite, HTML, CSS and JavaScript.

## Run on Windows
1. Extract the ZIP and open the `sahithi_editable_portfolio` folder in VS Code.
2. Open Terminal → New Terminal.
3. Run `py -m venv .venv`
4. Activate it in PowerShell: `.\.venv\Scripts\Activate.ps1`
   - If PowerShell blocks this, use Command Prompt terminal and run `.venv\Scripts\activate.bat`
5. Run `py -m pip install -r requirements.txt`
6. Run `py app.py`
7. Open `http://127.0.0.1:5000` in your browser.

## Admin
- Open `http://127.0.0.1:5000/admin/login`
- Username: `sahithi`
- Password: `ChangeMe123!`

Use the dashboard to edit your profile, add skills/projects/certificates, and delete entries. Data persists in `instance/portfolio.db`.

## Important
These credentials and the Flask development server are for local coursework/demo use only. Before public deployment, set strong `ADMIN_USERNAME`, `ADMIN_PASSWORD`, and `SECRET_KEY` environment variables; use HTTPS and a production server; add CSRF protection and login rate limiting. Do not publish the database or secrets.

## Personalize before submission
Update the profile and replace example/generic project links in the admin dashboard with your real links. Ensure every listed project and credential is accurate. Read the code enough to explain the Flask routes, SQLite tables, HTML templates and CSS.


### Professional sections update
The public portfolio now includes an editable Experience & Involvement section and no longer displays the creative-writing section. Add only accurate internships, volunteering, leadership, or professional experience through the admin dashboard.
