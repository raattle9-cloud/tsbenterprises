# Health Check Cron Job Setup

## Overview
This system implements an automated health check that pings your backend every 10 minutes to keep it alive. This is especially useful on platforms like Render that have inactivity timeouts.

## What Was Added

### 1. **New Dependency**
- Added `apscheduler>=3.10.0` to `requirements.txt`

### 2. **Health Check Endpoint**
- Location: `TSBv1/views.py` - `health_check()` view
- Endpoint: `GET /health/`
- Returns JSON response with status, message, and timestamp
- Example response:
  ```json
  {
    "status": "healthy",
    "message": "Backend is running",
    "timestamp": "2025-12-17T10:30:45.123456Z"
  }
  ```

### 3. **Scheduler Module**
- Location: `TSBv1/scheduler.py`
- Automatically starts background scheduler when Django app initializes
- Pings `/health/` endpoint every 10 minutes
- Logs all ping attempts and responses

### 4. **Management Command** (Optional)
- Location: `TSBv1/management/commands/health_check_scheduler.py`
- Can be run manually: `python manage.py health_check_scheduler`
- Useful for testing or running the scheduler in foreground

## How It Works

1. **Auto-start**: When Django starts, `TSBv1.apps.Tsbv1Config.ready()` is called
2. **Scheduler initialization**: The `start_scheduler()` function creates a background job
3. **Periodic pings**: Every 10 minutes, the scheduler calls `health_check_ping()`
4. **Health check**: Makes HTTP GET request to `/health/` endpoint
5. **Logging**: All responses are logged for monitoring

## Configuration

### Environment Variables (Optional)
Set these in your `.env` or Render dashboard:

```
BACKEND_URL=https://your-domain.com
RENDER=true  # Set automatically by Render
```

If `BACKEND_URL` is not set, defaults to `http://localhost:8000`

## Testing Locally

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Django server**:
   ```bash
   python manage.py runserver
   ```

3. **Verify health endpoint**:
   ```bash
   curl http://localhost:8000/health/
   ```

4. **Check logs** for health check pings (every 10 minutes)

## Monitoring

### Log Format
```
✓ Health check successful: 200
⚠ Health check returned status: 503
✗ Health check failed: Connection timeout
✗ Unexpected error in health check: [error message]
```

### Where to Find Logs
- **Locally**: Console output
- **Render**: Dashboard → Logs section
- **Production**: Check your logging backend/service

## Deployment to Render

1. Push your changes (especially `requirements.txt`)
2. Render will automatically reinstall dependencies
3. The scheduler will start automatically when your web service starts
4. Check Render logs to confirm: `✓ Health check scheduler started successfully`

## Disabling the Scheduler

If you need to disable the automatic scheduler:

1. Comment out the scheduler call in `TSBv1/apps.py`:
   ```python
   # start_scheduler()
   ```
2. Redeploy

## Advanced Configuration

### Change Ping Interval

Edit `TSBv1/scheduler.py`, line ~55:
```python
IntervalTrigger(minutes=10)  # Change 10 to desired minutes
```

### Change Health Check Behavior

Edit `TSBv1/scheduler.py`, `health_check_ping()` function to add custom logic, like:
- Checking database connectivity
- Verifying specific services
- Sending notifications on failures

### Multiple Instances

On Render with multiple instances, each instance will run its own scheduler independently. This is fine for health checks.

## Troubleshooting

### Scheduler not starting?
1. Check logs for errors during app initialization
2. Verify `apscheduler` is installed: `pip list | grep apscheduler`
3. Check that `TSBv1` is in `INSTALLED_APPS` in settings.py

### Health endpoint returning 404?
1. Verify URL pattern is added to `TSBv1/urls.py`
2. Restart Django server
3. Check `TSBv1/views.py` has `health_check()` function

### Ping failing with connection errors?
1. Verify `BACKEND_URL` environment variable is set correctly
2. Check that the backend is actually running
3. Verify firewall/network allows outbound requests

## Security Notes

- The `/health/` endpoint is publicly accessible (no authentication)
- This is intentional for monitoring/uptime checks
- If you want to restrict it, add authentication to the view
- Consider rate-limiting if concerned about abuse

## Next Steps

- Monitor logs to ensure pings are working
- Set up alerts if health checks start failing
- Consider adding database health checks for more robust monitoring
