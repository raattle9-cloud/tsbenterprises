# Quick Vercel Deployment Steps

## 🚀 Quick Start (5 Minutes)

### 1. Install Vercel CLI (if using CLI)
```bash
npm install -g vercel
```

### 2. Login to Vercel
```bash
vercel login
```

### 3. Deploy
```bash
vercel --prod
```

### 4. Set Environment Variables in Vercel Dashboard

Go to your project → Settings → Environment Variables and add:

**Required:**
- `DATABASE_URL` - Your Supabase PostgreSQL connection string
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_KEY` - Your Supabase service role key
- `SECRET_KEY` - Generate a new Django secret key (see below)

**Optional:**
- `SUPABASE_MEDIA_BUCKET` - Default: 'media'
- `SUPABASE_MEDIA_PUBLIC` - Set to 'true'
- `RAZORPAY_KEY_ID` - If using Razorpay
- `RAZORPAY_KEY_SECRET` - If using Razorpay

### 5. Generate Secret Key
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 6. Run Migrations
After first deployment, run:
```bash
vercel env pull .env.local
python manage.py migrate
```

Or connect to your production database and run migrations.

---

## 📋 Files Created

✅ `vercel.json` - Vercel configuration
✅ `api/index.py` - Serverless function entry point  
✅ `.vercelignore` - Files to exclude from deployment
✅ `TSB/settings.py` - Updated for Vercel compatibility

## 📖 Full Documentation

See `VERCEL_DEPLOYMENT.md` for detailed instructions and troubleshooting.

---

## ⚠️ Important Notes

1. **Secret Key**: Update `SECRET_KEY` in production (currently insecure)
2. **Database**: Ensure Supabase allows connections from Vercel
3. **Static Files**: Will be served automatically via Vercel CDN
4. **Media Files**: Should use Supabase storage (already configured)
5. **Timeouts**: Free tier has 10-second function timeout

---

## 🔗 Useful Links

- Vercel Dashboard: https://vercel.com/dashboard
- Project Settings: https://vercel.com/[your-username]/[your-project]/settings
- Function Logs: Available in Vercel Dashboard → Functions tab
