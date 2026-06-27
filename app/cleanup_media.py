from __future__ import annotations

import os
from typing import Iterable

from django.conf import settings

from .models import ProductoImagen


def delete_orphan_producto_images(*, media_root: str | None = None) -> int:
    """Elimina archivos en `media/productos/` que no estén referenciados en BD.

    Retorna la cantidad de archivos borrados.
    """

    media_root = str(media_root or settings.MEDIA_ROOT)

    # Asegura que existe la carpeta
    base_dir = os.path.join(media_root, "productos")
    if not os.path.isdir(base_dir):
        return 0

    referenced_names: set[str] = set(
        ProductoImagen.objects.values_list("imagen", flat=True)
    )

    deleted = 0
    for filename in os.listdir(base_dir):
        full_path = os.path.join(base_dir, filename)

        # Solo archivos regulares
        if not os.path.isfile(full_path):
            continue

        # referenced_names usa rutas relativas tipo "productos/xxx.jpg"
        rel_name = f"productos/{filename}"
        if rel_name not in referenced_names:
            try:
                os.remove(full_path)
                deleted += 1
            except OSError:
                # No rompemos el flujo de la app si algo falla
                pass

    return deleted


def borrar_archivos_producto_no_referenciados(nombres_referenciados: Iterable[str], *, media_root: str | None = None) -> int:
    """Borra archivos en `media/productos/` que NO estén en nombres_referenciados.

    `nombres_referenciados` debe contener nombres relativos como "productos/xxx.jpg".
    """

    media_root = str(media_root or settings.MEDIA_ROOT)
    base_dir = os.path.join(media_root, "productos")
    if not os.path.isdir(base_dir):
        return 0

    referenced = set(nombres_referenciados)
    deleted = 0
    for filename in os.listdir(base_dir):
        full_path = os.path.join(base_dir, filename)
        if not os.path.isfile(full_path):
            continue
        rel_name = f"productos/{filename}"
        if rel_name not in referenced:
            try:
                os.remove(full_path)
                deleted += 1
            except OSError:
                pass
    return deleted

