from django.contrib import admin

# Register your models here.
from controlstock.models import Cliente, Producto, Venta, Destilado, Provincia, Proveedor, Insumo, Compra, Venta_Producto, Compra_Insumo

admin.site.register(Cliente)
admin.site.register(Producto)
admin.site.register(Destilado)
admin.site.register(Provincia)

admin.site.register(Proveedor)
admin.site.register(Insumo)



class VentaInline(admin.TabularInline):
    model =Venta_Producto

class CompraInline(admin.TabularInline):
    model = Compra_Insumo


class FacturaVentaAdmin(admin.ModelAdmin):
    inlines = [
        VentaInline,
        ]
    
class FacturaCompraAdmin(admin.ModelAdmin):
    inlines = [
        CompraInline,
        ]

admin.site.register(Venta, FacturaVentaAdmin)
admin.site.register(Compra, FacturaCompraAdmin)

#con este código estás configurando el panel de administración de Django 
#para que al visualizar o editar una  Factura , 
#también se puedan ver y editar las ventas (el pedido)  relacionados en la misma página, 
#gracias al uso de  VentaInline  como una línea incrustada en la 
#interfaz de administración de  Factura 

