"""
Vercel serverless function entry point for Django application.
Vercel's Python runtime automatically wraps WSGI applications, so we just need to expose the app.
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TSB.settings')

# Mark that we're running on Vercel
os.environ['VERCEL'] = '1'

# Import Django after path is set
import django
django.setup()

from django.core.wsgi import get_wsgi_application

# Expose WSGI application as 'app' (Vercel's Python runtime expects this)
app = get_wsgi_application()
