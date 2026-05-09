# -----------------------------------------------------------------------
# Health check scheduler — DISABLED
#
# This used APScheduler + requests to ping /health/ every 10 min to keep
# the Render free-tier dyno alive. It caused "Connection refused" errors
# locally and added unnecessary third-party dependencies.
#
# Use an external free cron service instead (no code changes needed):
#   - https://cron-job.org  (free, reliable)
#   - https://uptimerobot.com  (free, also monitors uptime)
# Point it at:  https://your-app.onrender.com/health/  every 10 minutes.
# -----------------------------------------------------------------------

# import os
# import logging
# import requests
# from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.triggers.interval import IntervalTrigger
#
# logger = logging.getLogger(__name__)
#
#
# def health_check_ping():
#     backend_url = os.getenv('BACKEND_URL', '').rstrip('/')
#     if not backend_url:
#         return
#     try:
#         response = requests.get(f'{backend_url}/health/', timeout=10)
#         if response.status_code != 200:
#             pass  # optionally log warning
#     except Exception:
#         pass
#
#
# def start_scheduler():
#     if not os.getenv('RENDER'):
#         return False
#     scheduler = BackgroundScheduler()
#     if not scheduler.running:
#         try:
#             scheduler.add_job(
#                 health_check_ping,
#                 IntervalTrigger(minutes=10),
#                 id='health_check_ping',
#                 name='Health Check Ping',
#                 replace_existing=True,
#             )
#             scheduler.start()
#             return True
#         except Exception:
#             return False
#     return True
