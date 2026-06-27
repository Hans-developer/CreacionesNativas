from django.urls import path
from django.contrib.auth.views import LogoutView

from .views import (
    CatalogoView,

    LoginAdministradorView,

    DashboardInicioView,
    PagoConfiguracionView,
    ProductoListView,
    ProductoCreateView,
    ProductoUpdateView,
    ProductoDeleteView,
    UsuarioListView,
    UsuarioCreateView,
    UsuarioUpdateView,
    UsuarioDeleteView,
    UsuarioToggleActiveView,
    CategoriaListView,
    CategoriaCreateView,
    CategoriaUpdateView,
    CategoriaDeleteView,
    GaleriaProductoView,
    SolicitarCodigoView,
    VerificarCodigoView,
)


urlpatterns = [
    path("", CatalogoView.as_view(), name="catalogo"),

    path("galeria/<int:pk>/", GaleriaProductoView.as_view(), name="producto_detalle"),


    # Logout usado por app/templates/app/base.html
    path("logout/", LogoutView.as_view(next_page="/"), name="logout"),

    path("dashboard/login/", LoginAdministradorView.as_view(), name="dashboard_login"),
    path("dashboard/", DashboardInicioView.as_view(), name="dashboard_inicio"),
    
    path("dashboard/olvide-mi-clave/", SolicitarCodigoView.as_view(), name="solicitar_codigo"),
    path("dashboard/verificar-codigo/", VerificarCodigoView.as_view(), name="verificar_codigo"),

    path(
        "dashboard/configuracion-pago/",
        PagoConfiguracionView.as_view(),
        name="dashboard_config_pago",
    ),


    path("dashboard/productos/", ProductoListView.as_view(), name="dashboard_productos"),
    path("dashboard/productos/crear/", ProductoCreateView.as_view(), name="dashboard_producto_crear"),
    path(
        "dashboard/productos/<int:pk>/editar/",
        ProductoUpdateView.as_view(),
        name="dashboard_producto_editar",
    ),
    path(
        "dashboard/productos/<int:pk>/eliminar/",
        ProductoDeleteView.as_view(),
        name="dashboard_producto_eliminar",
    ),

    path("dashboard/usuarios/", UsuarioListView.as_view(), name="dashboard_usuarios"),
    path("dashboard/usuarios/crear/", UsuarioCreateView.as_view(), name="dashboard_usuario_crear"),
    path(
        "dashboard/usuarios/<int:pk>/editar/",
        UsuarioUpdateView.as_view(),
        name="dashboard_usuario_editar",
    ),
    path(
        "dashboard/usuarios/<int:pk>/toggle-active/",
        UsuarioToggleActiveView.as_view(),
        name="dashboard_usuario_toggle_active",
    ),
    path(
        "dashboard/usuarios/<int:pk>/eliminar/",
        UsuarioDeleteView.as_view(),
        name="dashboard_usuario_eliminar",
    ),

    path("dashboard/categorias/", CategoriaListView.as_view(), name="dashboard_categorias"),
    path("dashboard/categorias/crear/", CategoriaCreateView.as_view(), name="dashboard_categoria_crear"),
    path(
        "dashboard/categorias/<int:pk>/editar/",
        CategoriaUpdateView.as_view(),
        name="dashboard_categoria_editar",
    ),
    path(
        "dashboard/categorias/<int:pk>/eliminar/",
        CategoriaDeleteView.as_view(),
        name="dashboard_categoria_eliminar",
    ),
]
