
import sys
import django
import djongo
import pymongo
import sqlparse

print(f"Python: {sys.version}")
print(f"Django: {django.get_version()}")
print(f"Djongo: {djongo.__version__ if hasattr(djongo, '__version__') else 'unknown'}")
print(f"Pymongo: {pymongo.__version__}")
print(f"Sqlparse: {sqlparse.__version__}")
