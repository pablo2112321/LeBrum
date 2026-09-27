from typing import Any

from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError


MAX_IMAGE_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_IMAGE_DIMENSION = 4096


def validate_image_upload(value: Any) -> None:
    """Valida tamaño, formato declarado y contenido real de la imagen."""
    if value.size > MAX_IMAGE_UPLOAD_BYTES:
        raise ValidationError('La imagen no puede superar los 5 MB.')

    content_type = getattr(value, 'content_type', None)
    allowed_types = {'image/jpeg', 'image/png', 'image/webp'}
    if content_type and content_type not in allowed_types:
        raise ValidationError('Solo se admiten imágenes JPEG, PNG o WebP.')

    try:
        value.seek(0)
        with Image.open(value) as image:
            image.verify()
            image_format = (image.format or '').upper()
            if image_format not in {'JPEG', 'PNG', 'WEBP'}:
                raise ValidationError('El contenido no es un formato de imagen permitido.')
            width, height = image.size
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValidationError('El archivo no contiene una imagen válida.') from exc
    finally:
        value.seek(0)

    if (
        width is not None
        and height is not None
        and (width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION)
    ):
        raise ValidationError('La imagen no puede superar 4096 píxeles por lado.')
