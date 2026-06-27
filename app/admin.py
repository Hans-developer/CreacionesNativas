from django.contrib import admin
from .models import Categoria, Producto, ProductoImagen, PagoConfiguracion

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre",)

class ProductoImagenInline(admin.TabularInline):
    model = ProductoImagen
    extra = 1

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "categoria", "precio")
    inlines = [ProductoImagenInline]


admin.site.register(PagoConfiguracion)
