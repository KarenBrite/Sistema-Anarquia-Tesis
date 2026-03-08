from django import forms
from .models import Producto, Destilado, Insumo, Venta , Venta_Producto, Compra , Compra_Insumo
from django.forms.models import inlineformset_factory 
from django.contrib.auth.forms import AuthenticationForm

class ContactForm(forms.Form):
    nombre = forms.CharField(max_length=100)
    correo = forms.EmailField()
    mensaje = forms.CharField(widget=forms.Textarea, max_length=1000)


#CLIENTES------------------------------------------------------------------------------------------------

#form PADRE
class ventaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['fecha','total' , 'id_cliente','anulado','descuento']
        widgets = {
            'fecha': forms.DateInput(),
#No podemos agregar attrs={'type': 'date'} porque no me lo devuelve cuando quiero editar la venta
            'total': forms.NumberInput(attrs={'class': 'form-control', 'id': 'total','readonly': 'readonly'}),
            'id_cliente': forms.Select(attrs={'class': 'form-control'}),
            'anulado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'descuento': forms.NumberInput(attrs={'class': 'form-control', 'id': 'descuento','onchange':'actualizarSubtotal()'}),
        }

#form HIJO
class venta_ProductoForm(forms.ModelForm):
    class Meta:
        model = Venta_Producto
        fields = ['id','id_producto', 'cantidad', 'precio_unitario','subtotal','id_venta']
        widgets = {
            'id': forms.HiddenInput(),
            'id_venta': forms.HiddenInput(),
            'id_producto': forms.Select(attrs={'class': 'form-control','onchange': 'cargarPrecio(this)'}),
            'cantidad': forms.NumberInput(attrs={'class': 'cantidad','onchange':'actualizarSubtotal()','min':'0'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'precio-unitario','onchange':'actualizarSubtotal()'}),
            'subtotal': forms.NumberInput(attrs={'class': 'subtotal','readonly': 'readonly'})
        }

ventaFormset = inlineformset_factory(
    Venta,
    Venta_Producto,
    form=venta_ProductoForm,
    extra=5,
    can_delete=True
)


class productoForm(forms.ModelForm):
    eliminar_imagen = forms.BooleanField(required=False, label="Eliminar imagen", initial=False)
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion','precio_unitario','stock', 'destilado','reutilizable' ,'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control','required':'required'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control','required':'required'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control','required':'required'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control','required':'required'}),
            'destilado': forms.Select(attrs={'class': 'form-control'}),
            'reutilizable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control w-100'}),
        }
        eliminar_imagen = forms.BooleanField(required=False, label="Eliminar Imagen")
    def __init__(self, *args, **kwargs):
        # Extraer el producto de kwargs para poder acceder a la imagen
        producto = kwargs.get('instance')
        super().__init__(*args, **kwargs)

        # Cambiar el label de la imagen si ya existe una imagen
        if producto and producto.imagen:
            self.fields['imagen'].label = 'Reemplazar imagen'

        # Si el producto tiene imagen, mostrar el checkbox para eliminar la imagen
        if not producto or not producto.imagen:
            del self.fields['eliminar_imagen']  # Eliminar el campo si no hay imagen


#PROVEEDORES----------------------------------------------------------------------------------------------------

#form PADRE
class compraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ['fecha','total' , 'id_proveedor','anulado']
        widgets = {
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'dd/mm/aaaa', 'type': 'text'}),
#No podemos agregar attrs={'type': 'date'} porque no me lo devuelve cuando quiero editar la venta
            'total': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly', 'id': 'total'}),
            'id_proveedor': forms.Select(attrs={'class': 'form-control'}),
            'anulado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }



#form HIJO
class compra_InsumoForm(forms.ModelForm):
    class Meta:
        model = Compra_Insumo
        fields = ['id','id_insumo', 'cantidad', 'id_compra','precio_unitario','subtotal']
        widgets = {
            'id': forms.HiddenInput(),
            'id_compra': forms.HiddenInput(),
            'id_insumo': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'cantidad','onchange':'actualizarSubtotal()', 'min': '0'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'precio-unitario','onchange':'actualizarSubtotal()', 'min': '0'}),
            'subtotal': forms.NumberInput(attrs={'class': 'subtotal','readonly': 'readonly', 'min': '0'})
        }

compraFormset = inlineformset_factory(
    Compra,
    Compra_Insumo,
    form=compra_InsumoForm,
    extra=5,
    can_delete=True
)




class insumoForm(forms.ModelForm):
    class Meta:
        model = Insumo
        fields = ['insumo', 'cantidad', 'contenido_neto', 'unidad_medida', 'precio', 'fecha_de_vencimiento', 'id_proveedor' ]
        widgets = {
            'insumo': forms.TextInput(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'unidad_medida': forms.Select(attrs={'class': 'form-control'}),
            'contenido_neto': forms.NumberInput(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control'}),
            'fecha_de_vencimiento': forms.DateInput(),
            'id_proveedor': forms.Select(attrs={'class': 'form-control'}),
        }


class destiladoForm(forms.ModelForm):
    class Meta:
        model = Destilado
        fields = ['nombre', 'edicionlimitada']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'edicionlimitada': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['edicionlimitada'].label = "Edición Limitada"




#INICIO SESION------------------------------------------------------------------------------------------------

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label = 'Usuario',
        widget = forms.TextInput(attrs={'class': 'form-control','placeholder': 'Nombre de Usuario'
        })
                                                                     
    )

    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'Contraseña'
        })
    )