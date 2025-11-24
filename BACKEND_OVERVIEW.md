# Backend Overview & Admin Guide

## 1. Project at a glance
- **Root structure**: `manage.py`, `TSB` project package (global `settings`, `urls`, `wsgi/asgi`), and the single app `TSBv1`. Static assets sit under `static/` and `staticfiles/`.
- **Purpose**: A Django-powered storefront for TSB Enterprises, with service listings (Resorts, Waterparks, Dhaba etc.), user registration, cart/checkout flows, and Razorpay-based payments.
- **Core frameworks**: Django 5.0.14 (per `requirements.txt`) + Django REST framework (unused but installed), `gunicorn` and `whitenoise` for deployment, plus Razorpay integration.

## 2. Settings & configuration
- `TSB/settings.py` holds the common configuration:
  - `DEBUG=True` locally (switch to False and use env vars for production).
  - `SECRET_KEY` is hard-coded; swap it out for an environment variable before deploy.
  - Database: currently SQLite (`db.sqlite3`). For AWS or production, switch to PostgreSQL/RDS (the commented-out block shows the required fields).
  - Static/media: `STATIC_ROOT`/`MEDIA_ROOT` point to `static/`/`static/images` and `staticfiles/`. The service images live under `static/images/service/`.
  - Razorpay: live keys are defined at the bottom for payment processing.

## 3. The `TSBv1` app

### Models
- `Services`: catalog items (title, prices, description, `CATEGORY_CHOICES`, image upload path `service/`).
- `Customer`: profile extension for authenticated `User` records with address, city, state, mobile (validated as 10 digits), zipcode.
- `Cart`: links a `User` to a `Services` item plus quantity; helper `total_cost` calculates `quantity * discounted_price`.
- `Payment`: records Razorpay metadata plus a `paid` flag.
- `OrderPlaced`: ties together `User`, `Customer`, `Services`, `Payment`, quantity, status (pending/success/failed), timestamp, and exposes `total_cost`.

### Views (business logic)
- Static pages (`home`, `index2`, `about`, `contact`, policies) simply render templates under `TSBv1/templates/app/`.
- `CategoryView` / `CategoryViewNoSlug` / `CategoryTitle`: filter services by category slug/title and render `category.html`. `CategoryDetail` shows a single service.
- Authentication flows:
  - `CustomerRegistrationView`: registration form saved via `CustomerRegistrationForm`.
  - `ProfileView`: GET loads a profile form; POST saves or updates `Customer`.
  - `logout_user`: logs out the current user and redirects to login.
- Shopping/cart flows:
  - `add_to_cart`: adds a service to the current user’s cart (redirects to `/cart` afterwards).
  - `show_cart`: shows `app/addtocart.html`, calculates total + razorpay amount (multiplied by 100 for paise).
  - `plus_cart`, `minus_cart`, `remove_cart`: AJAX handlers that adjust cart quantities, recalculate totals, and return JSON for frontend update.
- Checkout & payments:
  - `checkout`: renders `app/checkout.html`.
  - `payment_done`: finalizes payment references (order_id, payment_id, cust_id) and renders `paymentdone.html`.

### URLs (`TSBv1/urls.py`)
- Public pages: `""`, `index2/`, `about/`, `contact/`, etc.
- Categorization: `category/`, `category/<slug:val>/`, `category-title/<val>`, `category-detail/<int:pk>/`.
- Cart & payment endpoints: `add-to-cart/`, `cart/`, `checkout/`, `pluscart/`, `minuscart/`, `removecart/`, `payments/`, `paymentdone/`.
- Auth endpoints: registration, login, password reset/change (using Django `auth_view` and custom forms).
- Admin login/out: `logout/`.
- Static/media serving is enabled via `static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)` at the bottom.

## 4. Admin interface (`TSBv1/admin.py`)
- Models registered: `Services`, `Customer`, `Cart`, `Payment`, `OrderPlaced`.
- Each model uses `list_display` to show key columns (e.g., `Services` shows title, price, category, image).
- **Usage**:
  1. Start the server (`python manage.py runserver`).
  2. Visit `http://127.0.0.1:8000/admin/`.
  3. Log in with the superuser credentials (you already have the ID/password).
  4. Manage services: add/edit `Services` entries, ensuring each has a `category` and `discounted_price`.
  5. Create `Customer` records (usually automatic via registration), inspect carts, payments, and orders.
- The admin is the easiest way to seed services that the public-facing `category` and `category-detail` pages depend on.

## 5. Service section and flow
- Templates in `TSBv1/templates/app/` (e.g., `index.html`, `category.html`, `categorydetail.html`) pull data from the views above.
- `category/` lists every service (no slug), `category/<slug>` filters by category code (`RE`, `WP`, etc.), and `category-detail/<id>` renders the details page for the given service.
- Static images for services live under `static/images/service/`; when you add a service in the admin, upload one of these images or new ones.
- Pagination or search logic isn’t implemented; filtering relies on `category` choices and `title`.

## 6. Running locally
1. Create & activate the virtual env:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. Apply migrations:
   ```powershell
   python manage.py migrate
   ```
4. Create a superuser (if needed):
   ```powershell
   python manage.py createsuperuser
   ```
5. Start the dev server:
   ```powershell
   python manage.py runserver 0.0.0.0:8000
   ```
6. Visit `/category/` and `/category-detail/<id>/` to confirm service pages render.

## 7. What Django admin gives you
- Fast CRUD for all key data models: services, customers, carts, payments, and orders.
- A quick way to inspect the cart contents and status of Razorpay payments without hitting the frontend.
- Central place to configure services that the public pages rely on.
- Superuser-only access; only authenticated admins can add services/orders.

## 8. Next steps & deployment pointers
- **Production**: swap SQLite for PostgreSQL (see the commented block in `settings.py`), use env vars for secrets, and set `DEBUG=False`.
- **Static files**: run `python manage.py collectstatic` and serve the outputs from Nginx/S3 via `whitenoise` or a CDN.
- **Payments**: Razorpay keys are already configured; ensure you’re not exposing them publicly beyond admin/environment files.
- **Monitoring**: Use Django logging + AWS (CloudWatch) if you deploy to EC2, EB, or App Runner.




