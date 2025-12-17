from django.apps import AppConfig


class Tsbv1Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'TSBv1'
    
    def ready(self):
        """
        Initialize the health check scheduler when the app is ready.
        """
        try:
            from .scheduler import start_scheduler
            start_scheduler()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Failed to start scheduler: {str(e)}')
