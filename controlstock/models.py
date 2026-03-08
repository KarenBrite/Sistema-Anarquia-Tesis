from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal

# Create your models here.

##########CONTROL STOCK

class Provincia(models.Model):
    nombre = models.CharField(max_length=20)

    def __str__(self):
        return self.nombre

class Cliente(models.Model):
    fecha = models.DateField(auto_now_add= True)
    nombre = models.CharField(max_length=30, help_text="cliente1")
    telefono = models.CharField(max_length=15)
    TIPO_CLIENTE = [
        ("C", "Consumidor Final"),
        ("R", "Responsable Inscripto"),
        ("M", "Monotributista"),
        ]
    tipo_cliente = models.CharField(max_length=1, choices=TIPO_CLIENTE, default="C")
    razon_social = models.CharField(max_length=30,default=None, null=True, blank=True)
    direccion = models.CharField(max_length=30, help_text="Introduce direccion de tu punto de venta", default=None, null=True, blank=True)
    cliente_mayorista = models.BooleanField(default=False)
    punto_venta = models.BooleanField(default=False)
    codPostal = models. IntegerField(verbose_name = "Codigo Postal")
    email = models.EmailField(default=None, null=True, blank=True)
    instagram = models.URLField(default=None, null=True, blank=True)
    provincia = models.ForeignKey(Provincia, on_delete=models.PROTECT)


    def __str__(self):
        return self.nombre
    
    
class Destilado(models.Model):
    nombre = models.CharField(max_length=30)
    edicionlimitada =  models.BooleanField(default=False)
    

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=30)  # Cambié esto para que sea un CharField
    descripcion = models.CharField(max_length=1000)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    reutilizable = models.BooleanField()
    destilado = models.ForeignKey('Destilado', on_delete=models.PROTECT, null=True, blank=True)  # Permitir valores nulos
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    
    def __str__(self):
        return self.nombre

#Venta
class Venta(models.Model):
    fecha = models.DateTimeField() 
    total = models.DecimalField(max_digits=10, decimal_places=2)
    anulado = models.BooleanField(default=False)
    id_cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)


#entidad intermedia -------------
class Venta_Producto(models.Model):
    id_venta = models.ForeignKey(Venta, on_delete=models.PROTECT)
    id_producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

###############PROVEEDORES
class Proveedor(models.Model):
    nombre = models.CharField(max_length=30)
    telefono = models.CharField(max_length=15)
    direccion = models.CharField(max_length=100)
    email = models.EmailField()
    
    def __str__(self):
        return self.nombre
    #insumos_venta = models.CharField(max_length=50)
    
    
class Compra(models.Model):
    fecha = models.DateTimeField()
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    anulado = models.BooleanField(default=False)
    #relacion
    id_proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT)

class Insumo(models.Model):
    UNIDADES_MEDIDA = [
        ('Lts', 'Litros'),
        ('Ml', 'Mililitros'),
        ('Kg', 'Kilogramos'),
        ('Gr', 'Gramos'),
        ('Un', 'Unidades'),
        ('', 'Sin especificar'),
    ]
    insumo = models.CharField(max_length=30, unique=True)
    cantidad = models.IntegerField()
    unidad_medida = models.CharField(
        max_length=5,
        choices=UNIDADES_MEDIDA,
        blank=True,
        null=True,
        default=''
    )
    contenido_neto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,   # Permite dejarlo vacío en el formulario
        null=True     # Permite que sea null en la base de datos
    )
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_de_vencimiento = models.DateField(blank=True, null=True)

    def clean(self):
        # Validación para asegurarse de que la cantidad no sea negativa
        if self.cantidad < 0:
            raise ValidationError("La cantidad no puede ser negativa.")

        # Validación para asegurarse de que el precio no sea negativo
        if self.precio < 0:
            raise ValidationError("El precio no puede ser negativo.")
     # Relación con Proveedor (Un insumo tiene un solo proveedor)
    id_proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='insumos')\
    
    def clean(self):
        # Redondear contenido_neto para eliminar los ceros innecesarios
        if self.contenido_neto is not None:
            self.contenido_neto = self.contenido_neto.quantize(Decimal(1)) if self.contenido_neto % 1 == 0 else self.contenido_neto
    
    def __str__(self): 
        return f"{self.insumo} ({self.get_unidad_medida_display()})" if self.unidad_medida else self.insumo

    

#entidad intermedia -------------
class Compra_Insumo(models.Model):
    id_compra = models.ForeignKey(Compra, on_delete=models.PROTECT)
    id_insumo = models.ForeignKey(Insumo, on_delete=models.PROTECT)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)






