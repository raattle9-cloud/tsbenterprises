"""
Health check scheduler initialization.
This module starts the APScheduler when the Django app is ready.
"""
import os
import logging
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


def health_check_ping():
    """
    Performs a health check ping to the backend.
    This keeps the application alive on platforms like Render.
    """
    try:
        # Get the backend URL - if running locally, use localhost
        if os.getenv('RENDER'):
            # Running on Render - use the public URL or construct it
            backend_url = os.getenv('BACKEND_URL', 'http://localhost:8000')
        else:
            backend_url = 'http://localhost:8000'
        
        # Perform a simple health check ping
        response = requests.get(
            f'{backend_url}/health/',
            timeout=10
        )
        
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
    """
    # Check if scheduler is already running
    scheduler = BackgroundScheduler()
    
    # Only start if not already running
    if not scheduler.running:
        try:
            # Schedule the health check to run every 10 minutes
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
