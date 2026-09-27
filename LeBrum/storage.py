from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateMediaStorage(FileSystemStorage):
    """Almacenamiento fuera de MEDIA_ROOT para archivos sensibles."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('location', settings.PRIVATE_MEDIA_ROOT)
        kwargs.setdefault('base_url', None)
        super().__init__(*args, **kwargs)
