#!/bin/bash
set -e

echo "Starting Gunicorn on port $PORT"

exec gunicorn \
  TSB.wsgi:application \
  --bind 0.0.0.0:$PORT \
  --workers ${WEB_CONCURRENCY:-1} \
  --timeout 120
