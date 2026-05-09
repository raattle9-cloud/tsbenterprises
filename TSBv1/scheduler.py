"""
Health check scheduler initialization.
This module starts the APScheduler when the Django app is ready.
Only active on Render (to prevent free-tier sleep). Does nothing locally.
"""
import os
import logging
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


def health_check_ping():
    """
    Performs a health check ping to keep the Render free-tier dyno alive.
    Only runs when the RENDER environment variable is set.
    """
    # BACKEND_URL must be set on Render (e.g. https://your-app.onrender.com)
    backend_url = os.getenv('BACKEND_URL', '').rstrip('/')
    if not backend_url:
        logger.warning('Health check skipped: BACKEND_URL is not set.')
        return

    try:
        response = requests.get(f'{backend_url}/health/', timeout=10)
        if response.status_code == 200:
            logger.info(f'Health check successful: {response.status_code}')
        else:
            logger.warning(f'Health check returned status: {response.status_code}')
    except requests.RequestException as e:
        logger.error(f'Health check failed: {str(e)}')
    except Exception as e:
        logger.error(f'Unexpected error in health check: {str(e)}')


def start_scheduler():
    """
    Start the background scheduler for health checks.
    Only starts when running on Render — skipped locally to avoid errors.
    """
    # Skip entirely when not running on Render
    if not os.getenv('RENDER'):
        logger.debug('Scheduler skipped: not running on Render.')
        return False

    scheduler = BackgroundScheduler()

    if not scheduler.running:
        try:
            scheduler.add_job(
                health_check_ping,
                IntervalTrigger(minutes=10),
                id='health_check_ping',
                name='Health Check Ping',
                replace_existing=True
            )
            scheduler.start()
            logger.info('Health check scheduler started successfully')
            return True
        except Exception as e:
            logger.error(f'Failed to start health check scheduler: {str(e)}')
            return False
    else:
        logger.info('Health check scheduler is already running')
        return True
