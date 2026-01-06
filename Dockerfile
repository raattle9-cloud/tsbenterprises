# Use Python 3.11 slim
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    dnsutils \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Project files
COPY . .

# IPv4 preference (Supabase fix)
RUN echo "precedence ::ffff:0:0/96  100" >> /etc/gai.conf

# Collect static (build time = safe)
RUN python manage.py collectstatic --noinput

# Entrypoint
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]

