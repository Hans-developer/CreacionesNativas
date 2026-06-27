import random
from django.conf import settings
from django.core.mail import send_mail
from django.forms import CheckboxInput
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    RedirectView,
    TemplateView,
    UpdateView,
)
from django.views.generic.edit import FormView
from django.views.generic.edit import ModelFormMixin
from django.views.generic.edit import FormMixin
from django.views.generic.base import ContextMixin
from django.contrib import messages
from django.contrib.auth.views import LoginView

from django.db import transaction

from .forms import CategoriaForm, PagoConfiguracionForm, ProductoForm, ProductoImagenFormSet, CrearUsuarioForm
from .models import Categoria, PagoConfiguracion, Producto, ProductoImagen
from .cleanup_media import borrar_archivos_producto_no_referenciados, delete_orphan_producto_images


User = get_user_model()


# -----------------------------
# Catálogo público
# -----------------------------
class CatalogoView(ListView):
    model = Producto
    template_name = "app/index.html"
    context_object_name = "productos"

    def get_queryset(self):
        return (
            Producto.objects.all()
            .select_related("categoria")
            .prefetch_related("imagenes")
            .order_by("-id")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Asegurar que siempre exista la configuración global
        config = PagoConfiguracion.objects.first()
        if not config:
            config = PagoConfiguracion.objects.create()

        ctx["config_general"] = config
        ctx["whatsapp_numero"] = config.whatsapp_numero
        ctx["categorias"] = Categoria.objects.all().order_by("nombre")
        return ctx


class GaleriaProductoView(DetailView):
    model = Producto
    template_name = "app/producto_detalle.html"
    context_object_name = "producto"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx


# -----------------------------
# Login admin-only
# -----------------------------
class LoginAdministradorView(LoginView):
    template_name = "app/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("dashboard_inicio")

    def form_valid(self, form):
        user = form.get_user()
        if not (user and (user.is_staff or user.is_superuser)):
            form.add_error(None, "Acceso denegado. Debes ser administrador.")
            return self.form_invalid(form)
        return super().form_valid(form)


# -----------------------------
# Mixin de autorización
# -----------------------------
class AdministradorMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_staff or self.request.user.is_superuser
        )

    def handle_no_permission(self):
        return render(self.request, "app/login.html", status=403)


# -----------------------------
# Dashboard
# -----------------------------
@method_decorator(login_required, name="dispatch")
class DashboardInicioView(TemplateView):
    template_name = "app/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["productos"] = Producto.objects.prefetch_related("imagenes").all().order_by("-id")
        ctx["usuarios_cantidad"] = User.objects.count()
        return ctx


# -----------------------------
# Configuración global de pago (Panel)
# -----------------------------
class PagoConfiguracionView(LoginRequiredMixin, AdministradorMixin, View):
    template_name = "app/dashboard.html"

    def get(self, request):
        config = PagoConfiguracion.objects.first()
        if not config:
            config = PagoConfiguracion.objects.create()
        form = PagoConfiguracionForm(instance=config)

        return render(
            request,
            self.template_name,
            {
                "modo": "config_pago",
                "form": form,
                "config_pago": config,
                "productos": Producto.objects.prefetch_related("imagenes").all().order_by("-id"),
                "usuarios_cantidad": User.objects.count(),
            },
        )

    def post(self, request):
        config = PagoConfiguracion.objects.first()
        if not config:
            config = PagoConfiguracion.objects.create()
        form = PagoConfiguracionForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            return redirect("dashboard_config_pago")

        return render(
            request,
            self.template_name,
            {
                "modo": "config_pago",
                "form": form,
                "config_pago": config,
                "productos": Producto.objects.prefetch_related("imagenes").all().order_by("-id"),
                "usuarios_cantidad": User.objects.count(),
            },
        )


# -----------------------------
# CRUD Productos (CBV)
# -----------------------------
class ProductoListView(LoginRequiredMixin, AdministradorMixin, ListView):
    model = Producto
    template_name = "app/dashboard.html"
    context_object_name = "productos"

    def get_queryset(self):
        return Producto.objects.prefetch_related("imagenes").all().order_by("-id")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["modo"] = "productos_list"
        return ctx


class ProductoCreateView(LoginRequiredMixin, AdministradorMixin, CreateView):
    model = Producto
    template_name = "app/dashboard.html"
    form_class = ProductoForm
    success_url = reverse_lazy("dashboard_productos")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["modo"] = "producto_form"

        if self.request.POST:
            ctx["imagen_formset"] = ProductoImagenFormSet(
                data=self.request.POST,
                files=self.request.FILES,
            )
        else:
            ctx["imagen_formset"] = ProductoImagenFormSet()
        return ctx

    def form_valid(self, form):
        imagen_formset = ProductoImagenFormSet(
            data=self.request.POST,
            files=self.request.FILES,
        )

        if not imagen_formset.is_valid():
            return self.form_invalid(form)

        response = super().form_valid(form)

        imagen_formset.instance = self.object
        imagen_formset.save()

        return response


class ProductoUpdateView(LoginRequiredMixin, AdministradorMixin, UpdateView):
    model = Producto
    template_name = "app/dashboard.html"
    form_class = ProductoForm
    success_url = reverse_lazy("dashboard_productos")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["modo"] = "producto_form"

        if self.request.POST:
            ctx["imagen_formset"] = ProductoImagenFormSet(
                data=self.request.POST,
                files=self.request.FILES,
                instance=self.object,
            )
        else:
            ctx["imagen_formset"] = ProductoImagenFormSet(instance=self.object)

        return ctx

    @transaction.atomic
    def form_valid(self, form):
        # Guardamos los archivos actualmente asociados antes del update
        imagenes_previas = list(self.object.imagenes.all())
        prev_files = [img.imagen.name for img in imagenes_previas if img.imagen and img.imagen.name]

        imagen_formset = ProductoImagenFormSet(
            data=self.request.POST,
            files=self.request.FILES,
            instance=self.object,
        )

        if not imagen_formset.is_valid():
            return self.form_invalid(form)

        response = super().form_valid(form)
        imagen_formset.save()

        # Después del save, calculamos qué archivos quedaron realmente referenciados
        actuales = ProductoImagen.objects.filter(producto=self.object).values_list("imagen", flat=True)

        # Borrar los que existían antes y ya no están referenciados por ninguna imagen del producto
        # (Esto elimina huérfanos locales por reemplazo en edición)
        borrar_archivos_producto_no_referenciados(
            prev_files,
            nombres_referenciados=list(actuales),
        )

        return response


class ProductoDeleteView(LoginRequiredMixin, AdministradorMixin, DeleteView):
    model = Producto
    template_name = "app/dashboard.html"
    success_url = reverse_lazy("dashboard_productos")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["modo"] = "producto_delete"
        return ctx

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # 1) Elimina las filas de imágenes (CASCADE). La señal post_delete se encarga del borrado físico.
        imagenes = list(self.object.imagenes.all())
        for img in imagenes:
            img.delete()

        # 2) Elimina el producto.
        response = super().delete(request, *args, **kwargs)

        # 3) Limpieza extra: elimina huérfanos locales que pudieran quedar (robustez).
        try:
            delete_orphan_producto_images()
        except Exception:
            pass

        return response



# -----------------------------
# CRUD Categorías (CBV)
# -----------------------------
class CategoriaListView(LoginRequiredMixin, AdministradorMixin, ListView):
    model = Categoria
    template_name = "app/dashboard.html"
    context_object_name = "categorias"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["modo"] = "categorias_list"
        return ctx


class CategoriaCreateView(LoginRequiredMixin, AdministradorMixin, CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "app/dashboard.html"
    success_url = reverse_lazy("dashboard_categorias")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["modo"] = "categoria_form"
        return ctx


class CategoriaUpdateView(LoginRequiredMixin, AdministradorMixin, UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "app/dashboard.html"
    success_url = reverse_lazy("dashboard_categorias")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["modo"] = "categoria_form"
        return ctx


class CategoriaDeleteView(LoginRequiredMixin, AdministradorMixin, DeleteView):
    model = Categoria
    template_name = "app/dashboard.html"
    success_url = reverse_lazy("dashboard_categorias")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["modo"] = "categoria_delete"
        return ctx


class UsuarioListView(LoginRequiredMixin, AdministradorMixin, ListView):
    model = User
    template_name = "app/dashboard.html"
    context_object_name = "usuarios"

    def get_queryset(self):
        return User.objects.all().order_by("id")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["modo"] = "usuarios_list"
        return ctx


# -----------------------------
# Crear/Actualizar/Borrar Usuarios
# -----------------------------
from .forms import UsuarioUpdateForm


class UsuarioCreateView(LoginRequiredMixin, AdministradorMixin, FormView):
    template_name = "app/dashboard.html"
    form_class = CrearUsuarioForm
    success_url = reverse_lazy("dashboard_usuarios")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.save()
        messages.success(self.request, f"Usuario '{user.username}' creado exitosamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["modo"] = "usuarios_create"
        return ctx


class UsuarioUpdateView(LoginRequiredMixin, AdministradorMixin, UpdateView):
    model = User
    template_name = "app/dashboard.html"
    form_class = UsuarioUpdateForm
    success_url = reverse_lazy("dashboard_usuarios")

    def form_valid(self, form):
        if self.request.user == self.get_object():
            if not form.cleaned_data['is_active']:
                messages.error(self.request, "No puedes desactivar tu propia cuenta.")
                return self.form_invalid(form)
            if not form.cleaned_data['is_superuser'] and self.request.user.is_superuser:
                messages.error(self.request, "No puedes remover tu propio estado de superusuario.")
                return self.form_invalid(form)
        messages.success(self.request, f"Usuario '{self.get_object().username}' actualizado exitosamente.")
        return super().form_valid(form)


class UsuarioToggleActiveView(LoginRequiredMixin, AdministradorMixin, View):
    success_url = reverse_lazy("dashboard_usuarios")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["modo"] = "usuario_form"
        return ctx


class UsuarioDeleteView(LoginRequiredMixin, AdministradorMixin, DeleteView):
    model = User
    template_name = "app/dashboard.html"
    success_url = reverse_lazy("dashboard_usuarios")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["modo"] = "usuario_delete"
        return ctx


# -----------------------------
# Flujo de Código por Email (Custom)
# -----------------------------
class SolicitarCodigoView(View):
    template_name = "app/forgot_password.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get("email")
        user = User.objects.filter(email=email).first()

        if user:
            codigo = str(random.randint(100000, 999999))

            request.session['reset_codigo'] = codigo
            request.session['reset_email'] = email

            subject = "Tu código de acceso - Vaguara"
            message = f"Hola {user.username},\n\nTu código de seguridad para acceder al panel es: {codigo}\n\nSi no solicitaste esto, ignora el mensaje."

            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            return redirect("verificar_codigo")
        else:
            return render(request, self.template_name, {"error": "No existe un usuario con ese correo electrónico."})


class VerificarCodigoView(View):
    template_name = "app/verify_code.html"

    def get(self, request):
        if 'reset_codigo' not in request.session:
            return redirect("solicitar_codigo")
        return render(request, self.template_name)

    def post(self, request):
        codigo_ingresado = request.POST.get("codigo")
        codigo_real = request.session.get('reset_codigo')
        email = request.session.get('reset_email')

        if codigo_ingresado == codigo_real:
            user = User.objects.get(email=email)
            login(request, user)

            del request.session['reset_codigo']
            del request.session['reset_email']

            return redirect("dashboard_inicio")
        else:
            return render(request, self.template_name, {"error": "El código es incorrecto."})

