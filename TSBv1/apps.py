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

        # Fix for Python 3.14 + Django 4.1 Context.__copy__ bug
        # This prevents the 'super object has no attribute dicts' crash
        try:
            from django.template import context
            
            def fixed_base_copy(self):
                """Fixed copy for Python 3.14 compatibility"""
                duplicate = self.__class__.__new__(self.__class__)
                for key, value in self.__dict__.items():
                    setattr(duplicate, key, value)
                if hasattr(self, 'dicts'):
                    duplicate.dicts = self.dicts[:]
                return duplicate
            
            context.BaseContext.__copy__ = fixed_base_copy
            print("Applied Python 3.14 template context compatibility patch")
        except Exception as e:
            print(f"Failed to apply Python 3.14 patch: {e}")
