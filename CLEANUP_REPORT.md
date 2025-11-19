# Codebase Cleanup Report

## ✅ SAFE TO DELETE - Prisma/Node.js (No longer used)

Since you've migrated to Django with PostgreSQL, these are **completely safe to delete**:

1. **`prisma/` folder** - Contains Prisma schema (no longer needed)
   - `prisma/schema.prisma` - Prisma schema file

2. **`node_modules/` folder** - Only contains Prisma dependencies (~100MB+)
   - Can be regenerated with `npm install` if needed later

3. **`package.json`** - Only contains Prisma dependencies
4. **`package-lock.json`** - Prisma dependency lock file

**Reason**: No Python code imports or uses Prisma. All database operations now use Django ORM.

---

## ✅ SAFE TO DELETE - Duplicate/Redundant Files

### Root Level Duplicates (Django uses `TSB/` versions)

1. **`settings.py`** (root) - Duplicate of `TSB/settings.py`
   - Django uses `TSB.settings` (from `manage.py`)
   - Root version has different middleware config but isn't used

2. **`urls.py`** (root) - Identical to `TSB/urls.py`
   - Django uses `TSB.urls` (from `TSB/settings.py`)

3. **`asgi.py`** (root) - Identical to `TSB/asgi.py`
   - Both are identical, root one is redundant

4. **`wsgi.py`** (root) - Likely duplicate of `TSB/wsgi.py`
   - Check if identical, if so, root one is redundant

5. **`middleware.py`** (root) - Not used
   - Only referenced in root `settings.py` which isn't used
   - `TSB/settings.py` doesn't use this middleware

### Old Database File

6. **`db.sqlite3`** - Old SQLite database
   - You're now using PostgreSQL (Supabase)
   - This file is no longer needed

---

## ⚠️ REVIEW BEFORE DELETING - Documentation/Config Files

These might contain useful information:

1. **`UserData.sh`** - Shell script (check if needed for deployment)
2. **`serversideInstructions.txt`** - Server setup instructions (might be useful)
3. **`__init__.py`** (root) - Check if needed (might be for Python package structure)

---

## 📋 Summary

### Definitely Safe to Delete:
- ✅ `prisma/` folder
- ✅ `node_modules/` folder  
- ✅ `package.json`
- ✅ `package-lock.json`
- ✅ `settings.py` (root)
- ✅ `urls.py` (root)
- ✅ `asgi.py` (root)
- ✅ `wsgi.py` (root) - verify first
- ✅ `middleware.py` (root)
- ✅ `db.sqlite3`

### Total Space Saved: ~100-200MB+ (mostly from node_modules)

---

## 🔍 Notes

- Django project structure uses `TSB/` as the main settings module
- All active configuration is in `TSB/settings.py`
- No Prisma code exists in Python files
- Database migrations are handled by Django, not Prisma

