# Vercel Deployment Guide for TSB Enterprises

This guide will walk you through deploying your Django application to Vercel.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com) if you don't have one
2. **Vercel CLI** (optional but recommended): Install via npm
   ```bash
   npm install -g vercel
   ```
3. **Git Repository**: Your code should be in a Git repository (GitHub, GitLab, or Bitbucket)

## Important Notes

⚠️ **Vercel Limitations for Django:**
- Vercel serverless functions have a 10-second execution timeout on the free tier (60 seconds on Pro)
- Database connections should use connection pooling
- Static files are served via Vercel's CDN
- Media files should be stored externally (you're using Supabase, which is perfect)

## Step-by-Step Deployment

### Step 1: Prepare Your Environment Variables

Before deploying, make sure you have all required environment variables ready:

1. **Database Configuration:**
   - `DATABASE_URL` - Your Supabase PostgreSQL connection string
   - Format: `postgresql://user:password@host:port/database`

2. **Supabase Configuration:**
   - `SUPABASE_URL` - Your Supabase project URL
   - `SUPABASE_SERVICE_KEY` - Your Supabase service role key
   - `SUPABASE_MEDIA_BUCKET` - Your media bucket name (default: 'media')
   - `SUPABASE_MEDIA_PUBLIC` - Set to 'true' if media is public
   - `SUPABASE_MEDIA_PUBLIC_URL` - Public URL for media (optional)

3. **Django Configuration:**
   - `SECRET_KEY` - Django secret key (generate a new one for production!)
   - `DJANGO_SETTINGS_MODULE` - Set to 'TSB.settings' (already configured)

4. **Razorpay** (if using):
   - `RAZORPAY_KEY_ID` - Your Razorpay key ID
   - `RAZORPAY_KEY_SECRET` - Your Razorpay key secret

### Step 2: Update Secret Key for Production

⚠️ **IMPORTANT**: The current `SECRET_KEY` in `settings.py` is insecure. Generate a new one:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Save this key - you'll add it as an environment variable in Vercel.

### Step 3: Collect Static Files Locally (Optional)

You can collect static files locally to verify everything works:

```bash
python manage.py collectstatic --noinput
```

Note: Vercel will handle static files automatically, but this helps verify your setup.

### Step 4: Deploy via Vercel Dashboard (Recommended)

1. **Go to Vercel Dashboard:**
   - Visit [vercel.com](https://vercel.com)
   - Click "Add New Project"

2. **Import Your Repository:**
   - Connect your Git provider (GitHub, GitLab, or Bitbucket)
   - Select your repository
   - Click "Import"

3. **Configure Project:**
   - **Framework Preset**: Select "Other" or leave as default
   - **Root Directory**: Leave as `.` (root)
   - **Build Command**: Leave empty (Vercel will auto-detect)
   - **Output Directory**: Leave empty
   - **Install Command**: Leave empty

4. **Add Environment Variables:**
   Click "Environment Variables" and add all required variables:
   ```
   DATABASE_URL=postgresql://user:password@host:port/database
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_KEY=your-service-key
   SUPABASE_MEDIA_BUCKET=media
   SUPABASE_MEDIA_PUBLIC=true
   SECRET_KEY=your-generated-secret-key
   DJANGO_SETTINGS_MODULE=TSB.settings
   ```
   
   Also add Razorpay keys if needed:
   ```
   RAZORPAY_KEY_ID=your-key-id
   RAZORPAY_KEY_SECRET=your-key-secret
   ```

5. **Deploy:**
   - Click "Deploy"
   - Wait for the build to complete
   - Your app will be live at `https://your-project.vercel.app`

### Step 5: Deploy via Vercel CLI (Alternative)

1. **Login to Vercel:**
   ```bash
   vercel login
   ```

2. **Link Your Project:**
   ```bash
   vercel link
   ```
   - Follow the prompts to select/create a project

3. **Set Environment Variables:**
   ```bash
   vercel env add DATABASE_URL
   vercel env add SUPABASE_URL
   vercel env add SUPABASE_SERVICE_KEY
   vercel env add SECRET_KEY
   # Add other variables as needed
   ```
   For each variable, select the environments (Production, Preview, Development)

4. **Deploy:**
   ```bash
   vercel --prod
   ```

### Step 6: Run Database Migrations

After deployment, you need to run migrations. You can do this via:

**Option A: Vercel CLI (Recommended)**
```bash
vercel env pull .env.local
python manage.py migrate
```

**Option B: Vercel Functions**
Create a one-time migration script or use Vercel's function logs to run migrations.

**Option C: Local with Production Database**
Connect locally to your production database and run:
```bash
python manage.py migrate
```

### Step 7: Create Superuser (Optional)

If you need a superuser for the admin panel:

```bash
python manage.py createsuperuser
```

Or connect to your production database and create one.

### Step 8: Verify Deployment

1. Visit your Vercel deployment URL
2. Check that static files load correctly
3. Test key functionality (login, pages, etc.)
4. Check Vercel function logs for any errors

## Configuration Files Created

The following files have been created for Vercel deployment:

1. **`vercel.json`** - Vercel configuration
   - Routes all requests to the Django serverless function
   - Handles static and media file routing

2. **`api/index.py`** - Serverless function entry point
   - Converts Vercel requests to WSGI format
   - Processes requests through Django

3. **`.vercelignore`** - Files to exclude from deployment
   - Excludes development files, virtual environments, etc.

4. **`TSB/settings.py`** - Updated for Vercel
   - Auto-detects Vercel environment
   - Disables DEBUG in production
   - Configures ALLOWED_HOSTS

## Troubleshooting

### Issue: Static files not loading
- **Solution**: Ensure `collectstatic` runs during build or use WhiteNoise middleware (already configured)

### Issue: Database connection timeout
- **Solution**: 
  - Use connection pooling (already configured with `CONN_MAX_AGE`)
  - Ensure your Supabase database allows connections from Vercel IPs
  - Check that `DATABASE_URL` is correctly formatted

### Issue: 500 errors
- **Solution**: 
  - Check Vercel function logs in the dashboard
  - Verify all environment variables are set
  - Ensure `SECRET_KEY` is set
  - Check that database migrations have been run

### Issue: CSRF token errors
- **Solution**: 
  - Ensure `ALLOWED_HOSTS` includes your Vercel domain
  - Check that cookies are being set correctly
  - Verify HTTPS is enabled (Vercel handles this automatically)

### Issue: Media files not uploading
- **Solution**: 
  - Ensure Supabase storage is configured correctly
  - Verify `SUPABASE_SERVICE_KEY` has proper permissions
  - Check bucket policies in Supabase dashboard

## Post-Deployment Checklist

- [ ] All environment variables are set
- [ ] Database migrations are applied
- [ ] Static files are loading correctly
- [ ] Media uploads work (if applicable)
- [ ] Admin panel is accessible
- [ ] User authentication works
- [ ] Payment integration works (if applicable)
- [ ] Custom domain is configured (optional)
- [ ] SSL certificate is active (automatic with Vercel)

## Custom Domain Setup (Optional)

1. Go to your project settings in Vercel
2. Click "Domains"
3. Add your custom domain
4. Follow DNS configuration instructions
5. Wait for DNS propagation (can take up to 48 hours)

## Monitoring and Logs

- **Function Logs**: Available in Vercel Dashboard → Your Project → Functions
- **Analytics**: Available in Vercel Dashboard → Analytics (Pro plan)
- **Real-time Logs**: Use `vercel logs` command

## Next Steps

After successful deployment:
1. Set up monitoring and error tracking
2. Configure custom domain (if needed)
3. Set up CI/CD for automatic deployments
4. Configure backup strategy for database
5. Set up staging environment for testing

## Support

- Vercel Documentation: https://vercel.com/docs
- Django on Vercel: https://vercel.com/guides/deploying-django-with-vercel
- Vercel Community: https://github.com/vercel/vercel/discussions

---

**Note**: Remember to update your `SECRET_KEY` in production and never commit sensitive keys to your repository!
