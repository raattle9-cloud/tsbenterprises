"""
Management command to start the APScheduler for health check pings.
This keeps the backend alive by pinging it every 10 minutes.
"""
import os
import requests
import logging
from django.core.management.base import BaseCommand
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.conf import settings

logger = logging.getLogger(__name__)


def health_check_ping():
    """
    Performs a health check ping to the backend.
    This keeps the application alive on platforms like Render.
    """
    try:
        # Use the site URL from Django settings or construct it
        # backend_url = os.getenv('BACKEND_URL', 'http://localhost:8000')
        backend_url = "https://tsbenterprises.onrender.com/"
        
        # Simple ping endpoint - you can customize this
        response = requests.get(
            f'{backend_url}/health/',
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f'✓ Health check successful: {response.status_code}')
        else:
            logger.warning(f'⚠ Health check returned status: {response.status_code}')
            
    except requests.RequestException as e:
        logger.error(f'✗ Health check failed: {str(e)}')
    except Exception as e:
        logger.error(f'✗ Unexpected error in health check: {str(e)}')


class Command(BaseCommand):
    help = 'Start the APScheduler for periodic health checks'

    def handle(self, *args, **options):
        scheduler = BackgroundScheduler()
        
        # Schedule the health check to run every 10 minutes
        scheduler.add_job(
            health_check_ping,
            IntervalTrigger(minutes=10),
            id='health_check_ping',
            name='Health Check Ping',
            replace_existing=True
        )
        
        scheduler.start()
        self.stdout.write(
            self.style.SUCCESS(
                '✓ Health check scheduler started. '
                'Pinging backend every 10 minutes.'
            )
        )
        
        try:
            # Keep the scheduler running
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            scheduler.shutdown()
            self.stdout.write(
                self.style.WARNING('Health check scheduler stopped.')
            )
