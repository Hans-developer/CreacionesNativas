from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
# Cambiamos modelformset_factory por inlineformset_factory
from django.forms import inlineformset_factory 
from django.core.exceptions import ValidationError

from .models import Categoria, PagoConfiguracion, Producto, ProductoImagen

User = get_user_model()


class ProductoForm(forms.ModelForm):
    """Formulario para CRUD de Producto (sin imágenes)."""
    class Meta:
        model = Producto
        fields = ["categoria", "nombre", "precio", "descripcion"]


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "descripcion"]


# Cambiamos la clase base a BaseInlineFormSet
class ProductoImagenFormSetBase(forms.BaseInlineFormSet):
    """Reglas del formset de imágenes:
    - Exactamente 1 imagen obligatoria por producto.
    """
    
    def clean(self):
        # Ejecutamos el clean original para generar los cleaned_data
        super().clean()

        imagenes_validas = 0

        for form in self.forms:
            # Si el formulario está marcado para borrarse, no lo contamos
            if self.can_delete and self._should_delete_form(form):
                continue
            
            # Validamos si hay una imagen cargada en el formulario actual
            if form.cleaned_data and form.cleaned_data.get("imagen"):
                imagenes_validas += 1

        # Validar que exista al menos una imagen
        if imagenes_validas == 0:
            raise ValidationError(
                "Debe subir obligatoriamente una imagen para el producto."
            )
        
        # Validar que no existan más de una imagen
        if imagenes_validas > 1:
            raise ValidationError(
                "Solo se permite un máximo de 1 imagen por producto."
            )


# Reemplazamos modelformset_factory por inlineformset_factory
ProductoImagenFormSet = inlineformset_factory(
    Producto,              # Modelo Padre
    ProductoImagen,        # Modelo Hijo
    formset=ProductoImagenFormSetBase,
    fields=("imagen", "orden"),
    extra=1,               # Muestra una casilla vacía por defecto
    can_delete=True,
)


class PagoConfiguracionForm(forms.ModelForm):
    class Meta:
        model = PagoConfiguracion
        fields = [
            "whatsapp_numero", 
            "mostrar_whatsapp",

            "nosotros_texto", 
            "mostrar_nosotros",
            "direccion_mapa", 
            "mostrar_direccion",
            "local_email", 
            "mostrar_email",
            "facebook_link", 
            "mostrar_facebook",
            "instagram_link",
            "mostrar_instagram"
        ]



class CrearUsuarioForm(UserCreationForm):
    class Meta:
        model = User
        # Incluimos todos los campos necesarios, incluyendo las contraseñas que UserCreationForm espera.
        fields = ("username", "first_name", "last_name", "email", "is_active", "is_staff", "is_superuser")


class UsuarioUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "is_active", "is_staff", "is_superuser")