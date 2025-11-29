# TSB Enterprises (Django)

Short README with setup, run and deployment notes for the TSB Enterprises Django project.


## Project Overview

This repository is a Django application (project root contains `manage.py` and `TSB/settings.py`). The main app is `TSBv1` and the project uses Supabase (PostgreSQL) for database storage. The project includes Razorpay integration and has production-service snippets for Gunicorn + Nginx included in `TSB/settings.py` comments.

## Quick Prerequisites

- Python 3.10+ (use `py -3` on Windows)
- PowerShell (Windows)
- Git (if you want to fetch remote branches)

## Recommended (Windows PowerShell) Setup

Run from the repository root (example path): `C:\Users\krish\OneDrive\Desktop\tsb-enterprises`.

1) (Optional) Update from remote `zimaad` branch

```powershell
git fetch origin
git checkout zimaad
git pull origin zimaad
```

2) Create and activate a virtual environment

```powershell
py -3 -m venv .venv
# PowerShell activate
. .\.venv\Scripts\Activate
```

3) Create a `.env` file with your Supabase database connection string

```powershell
# Copy the example file
Copy-Item .env.example .env
# Then edit .env and add your Supabase DATABASE_URL
```

4) Upgrade pip and install requirements

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

5) Apply database migrations

```powershell
python manage.py migrate
```

5) (Optional) Create a superuser

```powershell
python manage.py createsuperuser
```

6) (Optional) Collect static files for production-like setup

```powershell
python manage.py collectstatic --noinput
```

7) Run the development server (bind to localhost)

```powershell
python manage.py runserver 127.0.0.1:8000
# or
python manage.py runserver 0.0.0.0:8000
```

Then browse to `http://127.0.0.1:8000` or `http://localhost:8000`.

Notes:
- `0.0.0.0` is a bind address; prefer `127.0.0.1` or `localhost` when opening in a browser.
- If PowerShell prevents activation, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
```

## Environment & Sensitive Settings

- The project currently contains values inside `TSB/settings.py` (including `SECRET_KEY` and Razorpay keys). For production, move secrets into environment variables or a `.env` file and load them via `python-dotenv` or your deployment system.
- Relevant settings:
  - `STATIC_ROOT` -> `staticfiles`
  - `MEDIA_ROOT` appears in the settings (note: file contains two `MEDIA_ROOT` assignments; verify which path you want in production)
  - `ALLOWED_HOSTS` -> add hostnames used in production
  - `DEBUG` -> set to `False` in production

Example `.env` placeholders (do NOT commit real keys):

```
# REQUIRED: Supabase PostgreSQL Connection String
# Get this from: Supabase Dashboard > Project Settings > Database > Connection String > URI
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres

# Optional: Supabase Storage Configuration
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key_here

# Optional: Django Secret Key (for production, generate a new one)
SECRET_KEY=your-secret-key

# Optional: Razorpay Keys
RAZORPAY_KEY_ID=rzp_test_xxx
RAZORPAY_KEY_SECRET=your-razorpay-secret
```


## Running Checks

Check the project for common Django issues:

```powershell
. .\.venv\Scripts\Activate
python manage.py check
```

If you changed model code and want to ensure no warnings (e.g. regex escape warnings):

```powershell
python -W default manage.py check
```

## Debugging & Troubleshooting

- If the server isn't reachable:
  - Ensure you used `127.0.0.1` or `localhost` in browser.
  - Use `netstat -ano | findstr ":8000"` (Windows) to see which process is listening.
  - If port is occupied, run `python manage.py runserver 127.0.0.1:8001` with a different port.

- If you see warnings about invalid escape sequences in regexes, use Python raw strings: e.g. `regex=r'^\d{10}$'`.

- Gunicorn is listed in `requirements.txt` but is not supported on Windows. For Windows deployments use a Windows-friendly WSGI server (for example `waitress`) or deploy to Linux for Gunicorn + Nginx.

## Production Deployment Notes

The `TSB/settings.py` file includes example systemd socket and service snippets for Gunicorn. Basic outline:

- Create a virtualenv on the server and install `requirements.txt`.
- Use Gunicorn to serve the Django WSGI application (Linux):

```
gunicorn --workers 3 --bind unix:/run/gunicorn.sock TSB.wsgi:application
```

- Use Nginx to proxy to Gunicorn and serve static files.

If you deploy to a cloud provider, secure secrets (do not keep live keys in the repo) and configure allowed hosts and HTTPS.

## Project Structure (high-level)

- `manage.py` — Django management script
- `TSB/` — project package with `settings.py`, `urls.py`, `wsgi.py`, `asgi.py`
- `TSBv1/` — main app (models, views, templates, migrations)
- `static/` and `staticfiles/` — static assets

## Common Commands Summary (PowerShell)

```powershell
# Activate venv
. .\.venv\Scripts\Activate

# Install requirements
pip install -r requirements.txt

# Migrate DB
python manage.py migrate

# Create admin
python manage.py createsuperuser

# Run server
python manage.py runserver 127.0.0.1:8000
```

## Contributing

- Fork, create a feature branch, run tests (if any), open a PR. Keep secrets out of commits.

## License & Contact

This README is informational — confirm license with the repository owner. For questions, contact the project maintainer.
