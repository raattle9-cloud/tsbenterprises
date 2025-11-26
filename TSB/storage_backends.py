import mimetypes
import logging
from functools import lru_cache

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile, File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

logger = logging.getLogger(__name__)

try:
    from supabase import Client, create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("Supabase package not installed. Supabase storage will not work.")


def _require_supabase_settings() -> None:
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        raise ImproperlyConfigured(
            "Supabase storage requires SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables."
        )


@lru_cache
def _get_bucket():
    if not SUPABASE_AVAILABLE:
        raise ImproperlyConfigured("Supabase package is not installed.")
    _require_supabase_settings()
    try:
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        return client.storage.from_(settings.SUPABASE_MEDIA_BUCKET)
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        raise ImproperlyConfigured(f"Failed to connect to Supabase: {e}")


@deconstructible
class SupabaseMediaStorage(Storage):
    """
    Minimal Django storage backend that saves files to Supabase Storage.
    """

    def __init__(self):
        self._bucket = None
        self._initialized = False
        try:
            _require_supabase_settings()
            self._bucket = _get_bucket()
            self._initialized = True
        except (ImproperlyConfigured, Exception) as e:
            logger.warning(f"Supabase storage not initialized: {e}")
            self._initialized = False
    
    @property
    def bucket(self):
        if not self._initialized or not self._bucket:
            raise ImproperlyConfigured(
                "Supabase storage is not properly configured. "
                "Check SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables."
            )
        return self._bucket

    def _normalize_path(self, path: str) -> str:
        """Normalize path to use forward slashes (required by Supabase)."""
        return path.replace("\\", "/")

    def _save(self, name: str, content: File) -> str:
        if not self._initialized:
            raise ImproperlyConfigured("Cannot save file: Supabase storage is not configured.")
        # Normalize path to use forward slashes (Windows uses backslashes)
        normalized_name = self._normalize_path(name)
        data = content.read()
        content_type, _ = mimetypes.guess_type(normalized_name)
        metadata = {"content-type": content_type or "application/octet-stream"}

        try:
            self.bucket.upload(path=normalized_name, file=data, file_options=metadata)
            return normalized_name
        except Exception as e:
            logger.error(f"Error uploading file {name} to Supabase: {e}")
            raise

    def _open(self, name: str, mode: str = "rb") -> ContentFile:
        if not self._initialized:
            raise ImproperlyConfigured("Cannot open file: Supabase storage is not configured.")
        try:
            normalized_name = self._normalize_path(name)
            response = self.bucket.download(normalized_name)
            return ContentFile(response)
        except Exception as e:
            logger.error(f"Error downloading file {name} from Supabase: {e}")
            raise

    def delete(self, name: str) -> None:
        if not self._initialized:
            logger.warning(f"Cannot delete file {name}: Supabase storage is not configured.")
            return
        try:
            normalized_name = self._normalize_path(name)
            self.bucket.remove([normalized_name])
        except Exception as e:
            logger.error(f"Error deleting file {name} from Supabase: {e}")

    def exists(self, name: str) -> bool:
        if not self._initialized:
            return False
        try:
            normalized_name = self._normalize_path(name)
            folder = normalized_name.rsplit("/", 1)[0] if "/" in normalized_name else ""
            filename = normalized_name.split("/")[-1]
            objects = self.bucket.list(path=folder or "")
            return any(obj.get("name") == filename for obj in objects)
        except Exception as e:
            logger.error(f"Error checking if file {name} exists in Supabase: {e}")
            return False

    def size(self, name: str) -> int:
        if not self._initialized:
            return 0
        try:
            normalized_name = self._normalize_path(name)
            folder = normalized_name.rsplit("/", 1)[0] if "/" in normalized_name else ""
            filename = normalized_name.split("/")[-1]
            objects = self.bucket.list(path=folder or "")
            for obj in objects:
                if obj.get("name") == filename:
                    metadata = obj.get("metadata") or {}
                    return metadata.get("size") or obj.get("size", 0)
            return 0
        except Exception as e:
            logger.error(f"Error getting size of file {name} from Supabase: {e}")
            return 0

    def url(self, name: str) -> str:
        """Get URL for the file. Returns empty string if Supabase is not configured."""
        if not self._initialized:
            logger.warning(f"Supabase not configured, cannot generate URL for {name}")
            return ""  # Return empty string instead of crashing
        
        try:
            normalized_name = self._normalize_path(name)
            if settings.SUPABASE_MEDIA_PUBLIC:
                public_base = settings.SUPABASE_MEDIA_PUBLIC_URL
                if public_base:
                    return f"{public_base.rstrip('/')}/{normalized_name.lstrip('/')}"
                return self.bucket.get_public_url(normalized_name)
            response = self.bucket.create_signed_url(path=normalized_name, expires_in=settings.SUPABASE_SIGNED_URL_EXPIRY)
            return response["signedURL"]
        except Exception as e:
            logger.error(f"Error generating Supabase URL for {name}: {e}")
            return ""  # Return empty string to prevent template crashes

