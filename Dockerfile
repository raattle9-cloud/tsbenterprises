# Use Python 3.11 slim image
FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    dnsutils \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Force IPv4 preference (Supabase fix)
RUN echo "precedence ::ffff:0:0/96  100" >> /etc/gai.conf

# Collect static files
RUN python manage.py collectstatic --noinput

# Create startup script (Render-compatible)
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Running database migrations..."\n\
python manage.py migrate --fake 2>/dev/null || echo "Migrations skipped or already applied"\n\
echo "Starting gunicorn..."\n\
exec gunicorn --bind 0.0.0.0:$PORT --workers ${WEB_CONCURRENCY:-3} TSB.wsgi:application\n\
' > /app/start.sh && chmod +x /app/start.sh

# Render does NOT require EXPOSE, but keeping it doesn't hurt
EXPOSE 8000

# Start app
CMD ["/bin/bash", "/app/start.sh"]
