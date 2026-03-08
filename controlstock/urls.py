from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.contrib.auth.views import LoginView
from .forms import LoginForm
from controlstock.views import ProductosLista , ProveedoresLista , InsumosLista , DestiladosLista , ClientesLista , VentasLista , ComprasLista
from django.urls import path
from .views import register, CustomPasswordResetView
from django.contrib.auth.views import PasswordResetDoneView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('index/', views.index, name='index'),
    path('', views.index, name='index'),

    #login-------------------------------------------------------------
    path('login/', LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=LoginForm
    ),  name='login'),
    path("register/", register, name="register"),
    path("passwordReset/", CustomPasswordResetView.as_view(), name="passwordReset"),
    path("passwordResetDone/", PasswordResetDoneView.as_view(template_name="registration/passwordResetDone.html"), name="passwordResetDone"),
    path('passwordResetConfirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='passwordResetConfirm'),
    path('passwordResetComplete/', auth_views.PasswordResetCompleteView.as_view(), name='passwordResetComplete'),

    #mail-----------------------------------------------------------------
    path('contact-us/', views.contact_us, name='contact_us'),

    #clientes-------------------------------------------------------------
    
    path('clientes/clientesLista/', ClientesLista.as_view(), name='clientesLista'),
    path('clientes/clienteDetalle/<int:pk>/', views.clienteDetalle, name='clienteDetalle'),
    path('clientes/eliminar/<int:pk>/', views.clienteEliminar, name='clienteEliminar'),
    path('clientes/crear/', views.clienteCrear, name='clienteCrear'),
    path('clientes/editar/<int:pk>/', views.clienteEditar, name='clienteEditar'),

    path('ventas/ventasLista/', VentasLista.as_view(), name='ventasLista'),
    path('ventas/ventaDetalle/<int:pk>/', views.ventaDetalle, name='ventaDetalle'),
    path('ventas/crear/', views.ventaCrear, name='ventaCrear'),
    path('ventas/editar/<int:pk>/', views.ventaEditar, name='ventaEditar'),
    path('generar_factura/<int:venta_id>/', views.generar_factura, name='generar_factura'),
    path('factura/<int:venta_id>/', views.ver_factura, name='ver_factura'),


    path("productos/productosLista/", ProductosLista.as_view(), name="productosLista"),
    path('productos/crear/', views.productoCrear, name='productoCrear'),
    path('productos/editar/<int:pk>/', views.productoEditar, name='productoEditar'),
    path('productos/<int:pk>/', views.productoDetalle, name='productoDetalle'),
    path('productos/eliminar/<int:pk>/', views.productoEliminar, name='productoEliminar'),

    #proveedores------------------------------------------------------------------

    path("proveedores/proveedoresLista/", ProveedoresLista.as_view(), name="proveedoresLista"),
    path('proveedores/proveedorDetalle/<int:pk>/', views.proveedorDetalle, name='proveedorDetalle'),
    path('proveedores/crear/', views.proveedorCrear, name='proveedorCrear'),
    path('proveedores/eliminar/<int:pk>/', views.proveedorEliminar, name='proveedorEliminar'),
    path('proveedores/editar/<int:pk>/', views.proveedorEditar, name='proveedorEditar'),

    path('compras/comprasLista/', ComprasLista.as_view(), name='comprasLista'),
    path('compras/compraDetalle/<int:pk>/', views.compraDetalle, name='compraDetalle'),
    path('compras/crear/', views.compraCrear, name='compraCrear'),
    path('compras/editar/<int:pk>/', views.compraEditar, name='compraEditar'),
    path('compras/insumos/<int:proveedor_id>/', views.obtener_insumos_por_proveedor, name='obtener_insumos_por_proveedor'),

    path('insumos/insumosLista/', InsumosLista.as_view(), name='insumosLista'),
    path('insumos/insumoDetalle/<int:pk>/', views.insumoDetalle, name='insumoDetalle'),
    path('insumos/crear/', views.insumoCrear, name='insumoCrear'),
    path('insumos/editar/<int:pk>/', views.insumoEditar, name='insumoEditar'),
    path('insumos/eliminar/<int:pk>/', views.insumoEliminar, name='insumoEliminar'),

    path('destilados/destiladosLista/', DestiladosLista.as_view(), name='destiladosLista'),
    path('destilados/crear/', views.destiladoCrear, name='destiladoCrear'),
    path('destilados/editar/<int:pk>/', views.destiladoEditar, name='destiladoEditar'),
    path('destilados/eliminar/<int:pk>/', views.destiladoEliminar, name='destiladoEliminar'),


] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)