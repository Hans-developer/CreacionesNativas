from django.db import models
from django.urls import reverse


class Categoria(models.Model):
    """Modelo para las secciones o categorías del catálogo."""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["nombre"]

    def __str__(self) -> str:
        return self.nombre


class Producto(models.Model):
    # Relación uno a muchos: un producto pertenece obligatoriamente a una categoría
    categoria = models.ForeignKey(
        Categoria, 
        on_delete=models.PROTECT, # PROTECT evita borrar una categoría si tiene productos asignados
        related_name="productos",
        verbose_name="Categoría"
    )
    nombre = models.CharField(max_length=200)
    precio = models.IntegerField(help_text="Precio en centavos (ej: 3000 para $3.000)")
    descripcion = models.TextField()

    # Código único autogenerado (ej: #0001)
    codigo = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        editable=False,
        blank=True,
        help_text="Código único del producto (autogenerado).",
    )

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["-id"]

    def __str__(self) -> str:
        return self.nombre

    def _generar_codigo(self) -> str:
        # Asegura el formato: # + 4 dígitos
        # Usamos el id para mantener la secuencia por creación (orden por id).
        if not self.id:
            # Si por alguna razón no existe id, evitamos generar un código inválido.
            return ""
        return f"#{self.id:04d}"

    def save(self, *args, **kwargs):
        # Guardar una vez para obtener el id si es nuevo.
        es_nuevo = self.pk is None
        super().save(*args, **kwargs)

        # Si el código no está definido, lo generamos usando el id.
        if not self.codigo:
            self.codigo = self._generar_codigo()
            # Guardar de nuevo solo si cambiamos el código.
            # update_fields evita re-ejecutar lógica innecesaria.
            super().save(update_fields=["codigo"])

    def get_absolute_url(self):
        return reverse("catalogo")



class PagoConfiguracion(models.Model):

    """Configuración global del panel.

    Se guarda una sola vez (1 fila). Si no existe, se crea al entrar al panel.
    """

    whatsapp_numero = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Número de WhatsApp en formato solo dígitos (ej: 5493512345678).",
    )


    mostrar_link_pago = models.BooleanField(default=True, verbose_name="Mostrar link de pago")
    mostrar_whatsapp = models.BooleanField(default=True, verbose_name="Mostrar WhatsApp")
    mostrar_nosotros = models.BooleanField(default=True, verbose_name="Mostrar sección Nosotros")
    mostrar_direccion = models.BooleanField(default=True, verbose_name="Mostrar dirección/Mapa")
    mostrar_email = models.BooleanField(default=True, verbose_name="Mostrar Email")
    mostrar_facebook = models.BooleanField(default=True, verbose_name="Mostrar Facebook")
    mostrar_instagram = models.BooleanField(default=True, verbose_name="Mostrar Instagram")

    nosotros_texto = models.TextField(
        blank=True, 
        default="",
        help_text="Breve descripción de la tienda para la sección 'Sobre Nosotros'."
    )

    direccion_mapa = models.TextField(
        blank=True,
        default="",
        help_text="Ingrese solo la dirección (ej: Av. Siempre Viva 742, Springfield)."
    )

    local_email = models.EmailField(blank=True, default="", help_text="Email de contacto del local.")
    facebook_link = models.URLField(blank=True, default="", help_text="Enlace a tu página de Facebook.")
    instagram_link = models.URLField(blank=True, default="", help_text="Enlace a tu perfil de Instagram.")

    class Meta:
        verbose_name = "Configuración de pago"
        verbose_name_plural = "Configuración de pago"

    def __str__(self) -> str:
        return "Configuración de pago"



class ProductoImagen(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="imagenes",
    )
    # Cambiado a obligatorio (quité blank=True, null=True) ya que configuramos tu sistema para exigir una imagen real
    imagen = models.ImageField(upload_to="productos/")
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Imagen de producto"
        verbose_name_plural = "Imágenes de producto"
        ordering = ["orden", "id"]

    def __str__(self) -> str:
        return f"{self.producto.nombre} - {self.id}"

    def delete(self, using=None, keep_parents=False):
        # Borra el archivo físico cuando se elimina la fila.
        storage = self.imagen.storage
        name = self.imagen.name
        super().delete(using=using, keep_parents=keep_parents)
        if name:
            try:
                storage.delete(name)
            except Exception:
                pass
