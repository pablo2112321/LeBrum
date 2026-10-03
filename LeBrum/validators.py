import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from django.conf import settings
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

    scanner = str(getattr(settings, 'PRIVATE_MEDIA_SCANNER', '')).strip()
    if scanner:
        scan_uploaded_file(value, scanner)


def scan_uploaded_file(value: Any, scanner: str) -> None:
    """Escanea un archivo temporal con ClamAV y rechaza resultados inseguros."""
    scanner_path = shutil.which(scanner) or (
        scanner if Path(scanner).is_file() else None
    )
    if not scanner_path:
        raise ValidationError('El escáner antivirus configurado no está disponible.')

    try:
        with tempfile.NamedTemporaryFile(suffix='.upload') as temporary_file:
            value.seek(0)
            shutil.copyfileobj(value, temporary_file)
            temporary_file.flush()
            result = subprocess.run(
                [scanner_path, '--no-summary', temporary_file.name],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValidationError('No fue posible completar el escaneo antivirus.') from exc
    finally:
        value.seek(0)

    if result.returncode == 1:
        raise ValidationError('El archivo fue rechazado por el escáner antivirus.')
    if result.returncode != 0:
        raise ValidationError('El escáner antivirus no pudo validar el archivo.')
