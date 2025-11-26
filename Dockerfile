# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies including DNS utilities
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

# Force IPv4 preference over IPv6 (fixes Supabase connection issues)
RUN echo "precedence ::ffff:0:0/96  100" >> /etc/gai.conf

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "TSB.wsgi:application"]

