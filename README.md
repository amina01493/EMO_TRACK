# Simple Flask Auth + Author Pages

Quick steps to run the app locally (PowerShell on Windows):

```powershell
# create virtual env (optional but recommended)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# install dependencies
python -m pip install -r requirements.txt

# run the app
python app.py

# open http://127.0.0.1:5000 in your browser
```

Notes:
- Use the web UI to register a user (registration page). Registered users become 'authors' and appear on the home page.
- The app uses a local SQLite database `site.db` created automatically on first run.
