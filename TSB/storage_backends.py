import mimetypes
from functools import lru_cache

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile, File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from supabase import Client, create_client


def _require_supabase_settings() -> None:
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        raise ImproperlyConfigured(
            "Supabase storage requires SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables."
        )


@lru_cache
def _get_bucket():
    _require_supabase_settings()
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    return client.storage.from_(settings.SUPABASE_MEDIA_BUCKET)


@deconstructible
class SupabaseMediaStorage(Storage):
    """
    Minimal Django storage backend that saves files to Supabase Storage.
    """

    def __init__(self):
        _require_supabase_settings()
        self.bucket = _get_bucket()

    def _save(self, name: str, content: File) -> str:
        data = content.read()
        content_type, _ = mimetypes.guess_type(name)
        metadata = {"content-type": content_type or "application/octet-stream"}

        self.bucket.upload(path=name, file=data, file_options=metadata)
        return name

    def _open(self, name: str, mode: str = "rb") -> ContentFile:
        response = self.bucket.download(name)
        return ContentFile(response)

    def delete(self, name: str) -> None:
        self.bucket.remove([name])

    def exists(self, name: str) -> bool:
        folder = name.rsplit("/", 1)[0] if "/" in name else ""
        filename = name.split("/")[-1]
        objects = self.bucket.list(path=folder or "")
        return any(obj.get("name") == filename for obj in objects)

    def size(self, name: str) -> int:
        folder = name.rsplit("/", 1)[0] if "/" in name else ""
        filename = name.split("/")[-1]
        objects = self.bucket.list(path=folder or "")
        for obj in objects:
            if obj.get("name") == filename:
                metadata = obj.get("metadata") or {}
                return metadata.get("size") or obj.get("size", 0)
        return 0

    def url(self, name: str) -> str:
        if settings.SUPABASE_MEDIA_PUBLIC:
            public_base = settings.SUPABASE_MEDIA_PUBLIC_URL
            if public_base:
                return f"{public_base.rstrip('/')}/{name.lstrip('/')}"
            return self.bucket.get_public_url(name)
        response = self.bucket.create_signed_url(path=name, expires_in=settings.SUPABASE_SIGNED_URL_EXPIRY)
        return response["signedURL"]

