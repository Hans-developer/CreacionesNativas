from __future__ import annotations

from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import ProductoImagen


@receiver(post_delete, sender=ProductoImagen)
def borrar_archivo_producto_imagen(sender, instance: ProductoImagen, **kwargs):
    """Borra el archivo físico cuando se elimina ProductoImagen.

    Esto evita huérfanos en media/productos/.
    """
    imagen = getattr(instance, "imagen", None)
    if not imagen:
        return

    name = getattr(imagen, "name", None)
    if not name:
        return

    try:
        imagen.delete(save=False)
    except Exception:
        # No rompemos el flujo del borrado del producto.
        pass

