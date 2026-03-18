
# TSB Enterprises (Django)

Short README with setup, run and deployment notes for the TSB Enterprises Django project.

## Project Overview

This repository is a Django application (project root contains `manage.py` and `TSB/settings.py`). The main app is `TSBv1` and the project uses MongoDB (via Djongo) for database storage and Cloudinary for media/image uploads. The project includes Razorpay integration for payments and has production-service snippets for Gunicorn + Nginx included in `TSB/settings.py` comments.

## Quick Prerequisites and constraints

- Python 3.10+ (use `py -3` on Windows)
- PowerShell (Windows) or a POSIX shell on Linux
- Git (if you want to fetch remote branches)
- MongoDB Atlas account (for database)
- Cloudinary account (for image/media storage)

## Recommended (Windows PowerShell) Setup

Run from the repository root (example path): `C:\Users\krish\OneDrive\Desktop\tsb-enterprises`.

1. (Optional) Update from remote `staffportal` branch

```powershell
git fetch origin
git checkout staffportal
git pull origin staffportal
```

2. Create and activate a virtual environment

```powershell
py -3 -m venv .venv
# PowerShell activate
. .\.venv\Scripts\Activate
```

3. Create a `.env` file with your database and service credentials

```powershell
# Copy the example file
Copy-Item .env.example .env
# Then edit .env and add your credentials (see Environment section below)
```

4. Upgrade pip and install requirements

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

5. Apply database migrations

```powershell
python manage.py migrate
```

6. (Optional) Create a superuser

```powershell
python manage.py createsuperuser
```

7. (Optional) Collect static files for production-like setup

```powershell
python manage.py collectstatic --noinput
```

8. Run the development server (bind to localhost)

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

- All secrets are loaded from a `.env` file via `python-dotenv`. Never commit real keys to the repo.
- Relevant settings:
  - `STATIC_ROOT` -> `staticfiles`
  - `MEDIA_ROOT` -> `static/images` (Cloudinary handles media uploads in production)
  - `ALLOWED_HOSTS` -> add hostnames used in production
  - `DEBUG` -> set to `False` in production

Example `.env` placeholders (do NOT commit real keys):

```
# REQUIRED: MongoDB Connection String
# Get this from: MongoDB Atlas > Connect > Drivers > Copy connection string
DATABASE_URL=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority

# REQUIRED: Cloudinary Configuration (for image storage)
# Get this from: Cloudinary Dashboard
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# PRODUCTION SETTINGS
DEBUG=False
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Razorpay Payment Gateway
RAZORPAY_KEY_ID=rzp_live_xxx
RAZORPAY_KEY_SECRET=your-razorpay-secret
```

## Admin Features

Access the Django admin panel at `/admin/` (requires superuser login).

### Hero Image Management

Manage the homepage hero carousel slides directly from the admin panel.

- **Navigate**: Admin → TSBv1 → Hero images
- **Add single image**: Click "Add Hero Image", upload image, set alt text, display order, and active status
- **Bulk upload**: Click the **"📷 Bulk Upload Images"** button on the hero images list page to upload multiple images at once. Alt text is auto-generated from filenames
- **Manage**: Toggle `is_active` to show/hide slides, adjust `display_order` to control sequence
- **Fallback**: If no active hero images exist, the homepage shows default static slides

### Trusted Partners Management

Manage the "Our Trusted Partners" logo carousel on the homepage.

- **Navigate**: Admin → TSBv1 → Trusted partners
- **Add single partner**: Click "Add Trusted Partner", upload logo, set name, optional website URL, display order, and active status
- **Bulk upload**: Click the **"🏢 Bulk Upload Logos"** button on the partners list page to upload multiple logos at once. Partner names are auto-generated from filenames
- **Manage**: Toggle `is_active` to show/hide logos, adjust `display_order` to control sequence
- **Links**: Optionally set a `website_url` — clicking the partner logo will open the URL in a new tab
- **Fallback**: If no active partners exist, the carousel shows default placeholder logos

### Services Management

- Add/edit/delete services with multiple images (up to 4 per service)
- Manage pricing, categories, and advance payment settings
- Image previews in the admin list view

### Advance Bookings & Staff Verification

- View and manage advance bookings with QR codes
- Staff verification portal at `/staff/verify/`
- Booking status tracking (Pending → Verified → Used)

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

- **Djongo/MongoDB migration issues**: If `makemigrations` generates `AlterField` operations that fail, you can safely remove them from the migration file — MongoDB is schema-less and doesn't enforce column types. Only keep `CreateModel` operations.

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

```
manage.py                  — Django management script
TSB/                       — project package
  ├── settings.py          — Django settings (DB, Cloudinary, Razorpay config)
  ├── urls.py              — root URL configuration
  ├── wsgi.py / asgi.py    — WSGI/ASGI entry points
TSBv1/                     — main application
  ├── models.py            — Services, HeroImage, TrustedPartner, Customer, Cart, Payment, etc.
  ├── admin.py             — Admin panel configuration with bulk upload support
  ├── views.py             — All view logic (home, services, cart, checkout, etc.)
  ├── urls.py              — app URL patterns
  ├── forms.py             — Django forms
  ├── templates/
  │   ├── app/             — frontend templates (index, services, checkout, etc.)
  │   └── admin/           — custom admin templates (bulk upload pages)
  ├── static/app/          — CSS, JS, images
  └── migrations/          — database migrations
static/ & staticfiles/     — collected static assets
```

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
