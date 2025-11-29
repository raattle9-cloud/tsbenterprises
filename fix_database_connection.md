# Fix Database Connection Error on Render

## Problem
```
OperationalError: connection to server at "2406:da18:243:7421:e703:97a3:58fe:4f4c", port 6543 failed: Network is unreachable
```

**Root Cause**: Render doesn't support outbound IPv6 connections, but your DATABASE_URL is resolving to an IPv6 address.

## ✅ Solution: Use Supabase Connection Pooler

### Step 1: Get the Correct Connection String

1. Go to your Supabase project: https://supabase.com/dashboard
2. Select your project
3. Go to **Settings** → **Database**
4. Scroll to **Connection String** section
5. Select **URI** tab
6. **IMPORTANT**: Choose **Connection Pooling** (not Direct Connection)
7. Copy the connection string - it should look like:

```
postgresql://postgres.wshlzeyfiwoqafaqjqpj:[YOUR-PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
```

Key points:
- ✅ Uses `pooler.supabase.com` (IPv4 compatible)
- ✅ Port `6543` (pooler port)
- ✅ Works with Render's infrastructure

### Step 2: Update DATABASE_URL in Render

1. Go to Render dashboard: https://dashboard.render.com
2. Select your `tsb-enterprises` service
3. Click **Environment** tab
4. Find `DATABASE_URL` variable
5. Click **Edit** or **Add** if it doesn't exist
6. Paste the connection pooler URL from Step 1
7. **Replace `[YOUR-PASSWORD]` with your actual database password**
8. Click **Save Changes**

### Step 3: Redeploy

1. In Render dashboard, click **Manual Deploy** → **Deploy latest commit**
2. Wait for deployment to complete
3. Check logs for successful database connection

## 🔍 Verify the Fix

After redeployment, you should see in the logs:
```
✓ Database connection established
✓ Gunicorn workers started
```

Visit your site: `https://tsb-enterprises.onrender.com/services/`

## 🚨 If You Still Get Errors

### Error: "password authentication failed"
- Double-check your password in the DATABASE_URL
- Make sure there are no special characters that need URL encoding
- Use `%40` for `@`, `%23` for `#`, etc.

### Error: "too many connections"
- You're using the pooler, so this shouldn't happen
- If it does, reduce the number of Gunicorn workers in your Dockerfile

### Error: "SSL connection required"
- Add `?sslmode=require` to the end of your DATABASE_URL:
  ```
  postgresql://user:pass@host:6543/postgres?sslmode=require
  ```

## 📝 Important Notes

### Why Connection Pooler?

| Feature | Direct Connection | Connection Pooler |
|---------|------------------|-------------------|
| **Port** | 5432 | 6543 |
| **IPv6** | Yes (doesn't work on Render) | No (IPv4, works on Render) |
| **Max Connections** | Limited | Pooled (better for serverless) |
| **Latency** | Lower | Slightly higher |
| **Recommended for** | Long-running apps with few connections | Web apps with many short connections |

### Update Your .env File (for local development)

If you want to use the pooler locally too, update your `.env` file:

```env
DATABASE_URL=postgresql://postgres.wshlzeyfiwoqafaqjqpj:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
```

But keep in mind: **Your local Docker setup works with IPv6**, so you can keep using the direct connection locally if you prefer.

## 🎯 Quick Checklist

- [ ] Get connection pooler URL from Supabase dashboard
- [ ] Verify it uses `pooler.supabase.com` hostname
- [ ] Verify port is `6543`
- [ ] Update `DATABASE_URL` in Render environment variables
- [ ] Include your actual database password
- [ ] Save changes in Render
- [ ] Trigger manual deployment
- [ ] Check deployment logs for success
- [ ] Test your site

## 🆘 Still Having Issues?

If you're still getting connection errors, share:
1. The exact error message from Render logs
2. Your DATABASE_URL format (with password hidden): `postgresql://user:***@host:port/db`
3. Your Supabase region (e.g., ap-southeast-1)

---

**Expected Result**: After following these steps, your Django app on Render should successfully connect to Supabase using IPv4! 🚀
