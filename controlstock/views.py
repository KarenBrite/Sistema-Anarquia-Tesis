from django.contrib import messages
from django.core.files.storage import default_storage
import os
from django.http import JsonResponse
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import render , get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from .models import Provincia , Cliente, Producto, Destilado, Proveedor, Insumo, Venta, Venta_Producto, Compra, Compra_Insumo
from controlstock.models import Cliente
from .forms import ContactForm, productoForm, insumoForm, destiladoForm , ventaForm , venta_ProductoForm, ventaFormset, compraForm, compra_InsumoForm, compraFormset
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django .views.generic import ListView
from django.utils import timezone
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import fonts
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
import json
from datetime import datetime, timedelta
from django.utils.timezone import make_aware

# Create your views here.

# ==================== FUNCIÓN HELPER PARA VALIDACIÓN DE PERMISOS ====================

def check_write_permission(request):
    """
    Valida permisos de escritura (POST, PUT, DELETE) en vistas protegidas.
    Permitirá GET normal, pero bloqueará cambios si el usuario no es staff.
    
    Retorna:
        - True: Tiene permiso para continuar
        - False: No tiene permiso, debe redirigir/retornar error
    """
    if request.method == 'POST' and not request.user.is_staff:
        messages.error(request, "🔒 Acceso Denegado: Solo lectura. No tienes permisos para realizar cambios en la base de datos.")
        return False
    return True


def index(request):
    productos = Producto.objects.all()
    context = {"productos": productos}

    # Verificamos si el usuario no está autenticado y si no tiene la cookie "first_visit"
    if not request.user.is_authenticated and not request.session.get('first_visit', False):
        # Establecemos la cookie de primera visita
        request.session['first_visit'] = True
    return render (request, "index.html", context)

    

def contact_us(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            nombre = form.cleaned_data['nombre']
            correo = form.cleaned_data['correo']
            mensaje = form.cleaned_data['mensaje']

            try:
                send_mail(
                    f'Nuevo mensaje de {nombre} ({correo})',
                    mensaje,
                    settings.EMAIL_HOST_USER,
                    [settings.EMAIL_HOST_USER],
                )
                return JsonResponse({'success': True, 'message': "Correo enviado con éxito."})
            except Exception as e:
                return JsonResponse({'success': False, 'error': f"Error al enviar el correo: {str(e)}"})

        return JsonResponse({'success': False, 'error': 'Formulario inválido, revisa los datos ingresados.'})

    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

class ClientesLista(ListView):
    model = Cliente
    template_name = 'clientes/clientesLista.html'
    context_object_name = 'clientes'
    paginate_by = 6

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        tipo_cliente = self.request.GET.get('tipo_cliente', '')

        clientes = Cliente.objects.all()

        # Aplicar búsqueda por nombre o razón social
        if query:
            clientes = clientes.filter(
                Q(nombre__icontains=query) |
                Q(razon_social__icontains=query)
            )

        # Filtrar según el tipo de cliente (mayorista o minorista)
        if tipo_cliente == 'mayorista':
            clientes = clientes.filter(Q(tipo_cliente='R') | Q(tipo_cliente='M'))
        elif tipo_cliente == 'minorista':
            clientes = clientes.filter(tipo_cliente='C')

        return clientes

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['tipo_cliente'] = self.request.GET.get('tipo_cliente', '')
        return context



def clienteDetalle(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    ventas = Venta.objects.filter(id_cliente=cliente) 
    
    context = {
        'cliente': cliente,
        'ventas': ventas, 
    }
    return render(request, 'clientes/clienteDetalle.html', context)


#--CRUD--

def clienteEliminar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        if not check_write_permission(request):
            return redirect('clientesLista')
        
        cliente.delete()
        messages.error(request, "Cliente eliminado con éxito.")
        return redirect('clientesLista')
    return render(request, 'clientes/clienteEliminar.html', {'cliente': cliente})

def clienteCrear(request):
    if request.method == 'POST':
        if not check_write_permission(request):
            return redirect('clientesLista')
        
        nombre = request.POST.get('nombre')
        telefono = request.POST.get('telefono')
        tipo_cliente = request.POST.get('tipo_cliente')
        razon_social = request.POST.get('razon_social')
        direccion = request.POST.get('direccion')
        cliente_mayorista = request.POST.get('cliente_mayorista') == 'on'
        punto_venta = request.POST.get('punto_venta') == 'on'
        codPostal = request.POST.get('codPostal')
        email = request.POST.get('email')
        instagram = request.POST.get('instagram')
        provincia_id = request.POST.get('provincia')

        try:
            provincia = Provincia.objects.get(id=provincia_id)
        except Provincia.DoesNotExist:
            return HttpResponse("Provincia no encontrada", status=400)

        Cliente.objects.create(
            nombre=nombre,
            telefono=telefono,
            tipo_cliente=tipo_cliente,
            razon_social=razon_social,
            direccion=direccion,
            cliente_mayorista=cliente_mayorista,
            punto_venta=punto_venta,
            codPostal=codPostal,
            email=email,
            instagram=instagram,
            provincia=provincia
        )
        messages.success(request, "Cliente creado con éxito.")
        return redirect('clientesLista')

    provincias = Provincia.objects.all()
    return render(request, 'clientes/clienteCrear.html', {'provincias': provincias})


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import ProtectedError
from .models import Cliente, Provincia

def clienteEditar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == 'POST':
        if not check_write_permission(request):
            return redirect('clientesLista')
        
        # Si se presionó el botón de eliminar
        if 'eliminar' in request.POST:
            try:
                cliente.delete()
                messages.success(request, f'El cliente "{cliente.nombre}" ha sido eliminado correctamente.')
                return redirect('clientesLista')
            except ProtectedError:
                messages.error(request, 'No se puede eliminar el cliente porque tiene ventas asociadas.')
                return redirect('clienteEditar', pk=cliente.pk)

        # Obtener valores nuevos del formulario
        nuevo_nombre = request.POST.get('nombre', '').strip()
        nuevo_telefono = request.POST.get('telefono', '').strip()
        nuevo_tipo_cliente = request.POST.get('tipo_cliente', '').strip()
        nuevo_razon_social = request.POST.get('razon_social', '').strip()
        nuevo_direccion = request.POST.get('direccion', '').strip()
        nuevo_cliente_mayorista = request.POST.get('cliente_mayorista') == 'on'
        nuevo_punto_venta = request.POST.get('punto_venta') == 'on'
        nuevo_codPostal = request.POST.get('codPostal', '').strip()
        nuevo_email = request.POST.get('email', '').strip()
        nuevo_instagram = request.POST.get('instagram', '').strip()
        nueva_provincia_id = request.POST.get('provincia')

        # Comparar valores actuales con los nuevos
        cambios_realizados = (
            (cliente.nombre or '') != nuevo_nombre or
            (cliente.telefono or '') != nuevo_telefono or
            (cliente.tipo_cliente or '') != nuevo_tipo_cliente or
            (cliente.razon_social or '') != nuevo_razon_social or
            (cliente.direccion or '') != nuevo_direccion or
            cliente.cliente_mayorista != nuevo_cliente_mayorista or
            cliente.punto_venta != nuevo_punto_venta or
            (cliente.codPostal or '') != nuevo_codPostal or
            (cliente.email or '') != nuevo_email or
            (cliente.instagram or '') != nuevo_instagram or
            (cliente.provincia.id if cliente.provincia else None) != (int(nueva_provincia_id) if nueva_provincia_id else None)
        )

        if cambios_realizados:
            # Actualizar datos si hubo cambios
            cliente.nombre = nuevo_nombre
            cliente.telefono = nuevo_telefono
            cliente.tipo_cliente = nuevo_tipo_cliente
            cliente.razon_social = nuevo_razon_social
            cliente.direccion = nuevo_direccion
            cliente.cliente_mayorista = nuevo_cliente_mayorista
            cliente.punto_venta = nuevo_punto_venta
            cliente.codPostal = nuevo_codPostal
            cliente.email = nuevo_email
            cliente.instagram = nuevo_instagram
            cliente.provincia = Provincia.objects.get(id=nueva_provincia_id) if nueva_provincia_id else None
            cliente.save()
            messages.success(request, f'El cliente "{cliente.nombre}" se ha actualizado correctamente.')
        else:
            messages.info(request, "No se han realizado cambios en el cliente.")

        return redirect('clientesLista')

    provincias = Provincia.objects.all()
    return render(request, 'clientes/clienteEditar.html', {
        'cliente': cliente,
        'provincias': provincias
    })



#VENTA ------------------------------------------------------------
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.generic import ListView
from .models import Venta

class VentasLista(ListView):
    model = Venta
    template_name = 'ventas/ventasLista.html'
    context_object_name = 'venta'
    paginate_by = 4  # Número de resultados por página

    def get_queryset(self):
        queryset = Venta.objects.all().order_by('-fecha')  # Orden inicial: más reciente primero

        # Búsqueda por nombre de cliente
        query = self.request.GET.get('q', '')
        if query:
            queryset = queryset.filter(id_cliente__nombre__icontains=query)

        # Filtrar por estado (anulado o no)
        filtro = self.request.GET.get('filtro', 'no')
        if filtro == 'si':
            queryset = queryset.filter(anulado=True)
        elif filtro == 'no':
            queryset = queryset.filter(anulado=False)

        # Filtrar por fecha
        filtro_fecha = self.request.GET.get('filtro_fecha', '')
        if filtro_fecha == 'ultimos_7':
            hace_siete_dias = datetime.now() - timedelta(days=7)
            queryset = queryset.filter(fecha__gte=hace_siete_dias)

        # Filtrar por mes y año
        filtro_mes = self.request.GET.get('filtro_fecha', 'todas')
        filtro_anio = self.request.GET.get('filtro_anio', str(datetime.now().year))  # Año actual por defecto

        if filtro_mes != 'todas' and filtro_mes.isdigit() and 1 <= int(filtro_mes) <= 12:
            mes = int(filtro_mes)
            año = int(filtro_anio)
            fecha_inicio = make_aware(datetime(año, mes, 1))

            if mes == 12:
                fecha_fin = make_aware(datetime(año + 1, 1, 1))  # Si es diciembre, el siguiente mes es enero del año siguiente
            else:
                fecha_fin = make_aware(datetime(año, mes + 1, 1))  # El primer día del siguiente mes

            queryset = queryset.filter(fecha__gte=fecha_inicio, fecha__lt=fecha_fin)
        elif filtro_anio.isdigit():  # Filtrar solo por año
            año = int(filtro_anio)
            fecha_inicio = make_aware(datetime(año, 1, 1))
            fecha_fin = make_aware(datetime(año + 1, 1, 1))
            queryset = queryset.filter(fecha__gte=fecha_inicio, fecha__lt=fecha_fin)

        # Ordenar por fecha (ascendente o descendente)
        ordenar = self.request.GET.get('ordenar', 'desc')
        if ordenar == 'asc':
            queryset = queryset.order_by('fecha')
        else:
            queryset = queryset.order_by('-fecha')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        meses_nombres = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]

        # Obtener años únicos de ventas para el filtro de año
        años_disponibles = Venta.objects.dates('fecha', 'year', order='DESC').values_list('fecha__year', flat=True)

        context.update({
            'filtro': self.request.GET.get('filtro', 'no'),
            'query': self.request.GET.get('q', ''),
            'filtro_fecha': self.request.GET.get('filtro_fecha', 'todas'),
            'filtro_anio': self.request.GET.get('filtro_anio', str(datetime.now().year)),
            'ordenar': self.request.GET.get('ordenar', 'desc'),
            'meses': enumerate(meses_nombres, start=1),  # (1, "Enero"), (2, "Febrero")...
            'años_disponibles': años_disponibles
        })

        # Paginación
        paginator = Paginator(self.get_queryset(), self.paginate_by)
        page = self.request.GET.get('page')

        try:
            context['venta'] = paginator.page(page)
        except PageNotAnInteger:
            # Si no es un número válido, muestra la primera página
            context['venta'] = paginator.page(1)
        except EmptyPage:
            # Si la página es mayor que el número de páginas, redirige a la última página
            context['venta'] = paginator.page(paginator.num_pages)

        # Si no hay ventas, agregar un mensaje de "no resultados"
        if not context['venta']:
            context['no_results'] = True

        return context


def ventaDetalle(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    
    # Crear el inline formset para los productos relacionados con la venta
    formset = ventaFormset(instance=venta)
    
    context = {
        'venta': venta,
        'formset': formset,  # Pasamos el formset al contexto
    }
    
    return render(request, 'ventas/ventaDetalle.html', context)

def ver_factura(request, venta_id):
    # Obtener la venta desde la base de datos o retornar 404 si no se encuentra
    venta = get_object_or_404(Venta, id=venta_id)
    
    # Obtener los productos relacionados con la venta
    venta_productos = Venta_Producto.objects.filter(id_venta=venta)
    
    # Calcular el total
    total = sum(venta_producto.id_producto.precio_unitario * venta_producto.cantidad for venta_producto in venta_productos)
    
    # Pasar los datos a la plantilla
    return render(request, 'factura.html', {
        'venta': venta,
        'venta_productos': venta_productos,
        'total': total
    })

def generar_factura(request, venta_id):
    # Obtener la venta desde la base de datos o retornar 404 si no se encuentra
    venta = get_object_or_404(Venta, id=venta_id)

    # Crear el objeto HttpResponse con el tipo de contenido PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="factura_{venta.id}.pdf"'

    # Crear el objeto Canvas para el archivo PDF
    c = canvas.Canvas(response, pagesize=letter)

    # Establecer fuente y color para el título
    c.setFont("Helvetica", 18)
    c.setFillColor(colors.black)
    c.drawString(100, 770, "Anarquía Gin - Detalle Venta")
    

    # Información de la factura
    c.setFont("Helvetica", 12)
    c.drawString(100, 730, f"Factura #: {venta.id}")
    c.drawString(400, 730, f"Fecha: {venta.fecha.strftime('%d/%m/%Y')}")

    # Información del cliente
    c.drawString(100, 710, f"Cliente: {venta.id_cliente.nombre}")
    c.drawString(100, 690, f"Dirección: {venta.id_cliente.direccion}")
    c.drawString(100, 670, f"Teléfono: {venta.id_cliente.telefono}")

    # Líneas separadoras
    c.setStrokeColor(colors.grey)
    c.setLineWidth(0.5)
    c.line(90, 655, 550, 655)

    # Títulos de la tabla de productos
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(100, 630, "Producto")
    c.drawString(300, 630, "Precio Unitario")
    c.drawString(420, 630, "Cantidad")
    c.drawString(500, 630, "Total")

    # Línea horizontal para separar la cabecera de la tabla
    c.setStrokeColor(colors.grey)
    c.setLineWidth(0.5)
    c.line(90, 625, 550, 625)

    # Obtener los productos relacionados con esta venta usando la tabla intermedia
    venta_productos = Venta_Producto.objects.filter(id_venta=venta)  # Filtrar por venta

    y_position = 610
    for venta_producto in venta_productos:
        producto = venta_producto.id_producto
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)
        c.drawString(100, y_position, producto.nombre)
        c.drawString(300, y_position, f"${producto.precio_unitario:.2f}")
        c.drawString(420, y_position, str(venta_producto.cantidad))
        c.drawString(500, y_position, f"${producto.precio_unitario * venta_producto.cantidad:.2f}")
        y_position -= 20

    # Línea horizontal antes del total
    c.setStrokeColor(colors.grey)
    c.line(90, y_position - 10, 550, y_position - 10)

    # Total de la factura
    total = sum(venta_producto.id_producto.precio_unitario * venta_producto.cantidad for venta_producto in venta_productos)
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)
    c.drawString(100, y_position - 30, f"Total: ${total:.2f}")

    # Guardar el PDF en la respuesta
    c.save()

    return response
    
#FUNCION CON FORMSET------------------
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
import json


def ventaCrear(request):
    productos = Producto.objects.all()
    productos_dict = {
        p.id: float(p.precio_unitario) for p in productos
    }

    if request.method == 'POST':
        if not check_write_permission(request):
            return render(request, 'ventas/ventaCrearForm.html', {
                'form': ventaForm(), 
                'ventaFormset': ventaFormset(queryset=Venta_Producto.objects.none()), 
                'productos': json.dumps(productos_dict)
            })
        
        form = ventaForm(request.POST)
        formset = ventaFormset(request.POST)

        if form.is_valid() and formset.is_valid():
            detalles_venta = formset.save(commit=False)  # No guardar todavía
            error_stock = False  # Bandera para verificar si hay error de stock

            # Validar stock antes de guardar la venta
            for detalle in detalles_venta:
                producto = detalle.id_producto
                if producto.stock < detalle.cantidad:
                    messages.error(request, f"No hay suficiente stock del producto {producto.nombre}.")
                    error_stock = True

            if error_stock:
                # Si hay error, mostrar el mensaje en el template sin perder los datos ingresados
                return render(request, 'ventas/ventaCrearForm.html', {
                    'form': form, 
                    'ventaFormset': formset, 
                    'productos': json.dumps(productos_dict)
                })

            # Guardar la venta después de validar stock
            venta = form.save()  # Guardar la venta y obtener el ID

            # Asignar la venta a los detalles y guardarlos
            for detalle in detalles_venta:
                detalle.id_venta = venta  # Asignar la relación con la venta
                detalle.save()

                # Actualizar stock
                detalle.id_producto.stock -= detalle.cantidad
                detalle.id_producto.save()

            messages.success(request, "Venta creada exitosamente.")
            return HttpResponseRedirect(reverse('ventasLista'))

    else:
        form = ventaForm()
        formset = ventaFormset(queryset=Venta_Producto.objects.none())

    return render(request, 'ventas/ventaCrearForm.html', {
        'form': form,
        'ventaFormset': formset,
        'productos': json.dumps(productos_dict)
    })


# ----------------------------------------
from django.urls import reverse
from .forms import ventaForm, ventaFormset

def ventaEditar(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    

    if request.method == 'POST':
        if not check_write_permission(request):
            form = ventaForm(instance=venta)
            formset = ventaFormset(instance=venta)
            productos = Producto.objects.all()
            productos_dict = {
                p["id"]: float(p["precio_unitario"])
                for p in productos.values("id", "precio_unitario")
            }
            context = {
                'form': form, 
                'venta': venta, 
                'ventaFormset': formset,
                'productos': json.dumps(productos_dict)
            }
            return render(request, 'ventas/ventaEditarForm.html', context)
        
        form = ventaForm(request.POST, instance=venta)
        formset = ventaFormset(request.POST, instance=venta)

        if form.is_valid() and formset.is_valid():
                        # Verificar si hubo cambios en el formulario o el formset
            if form.has_changed() or any(f.has_changed() for f in formset.forms):
                form.save()  # Guarda la venta
                formset.save()  # Guarda los productos relacionados
                messages.success(request, f'La venta "{venta.id}" se ha actualizado correctamente.')
                return HttpResponseRedirect(reverse('ventasLista'))
            else:
                # Si no hubo cambios
                messages.info(request, "No se han realizado cambios en la venta.")
                return HttpResponseRedirect(reverse('ventasLista'))
            #detalles_venta = formset.save(commit=False)  # No guardar aún

            # Devolver stock de los productos originales antes de calcular el nuevo stock
       #     for detalle in venta.detalle_venta.all():
        #        detalle.id_producto.stock += detalle.cantidad
         #       detalle.id_producto.save()

            # Validar stock con las nuevas cantidades
          #  for detalle in detalles_venta:
           #     producto = detalle.id_producto
            #    if producto.stock < detalle.cantidad:
             #       messages.error(request, f"No hay suficiente stock para el producto {producto.nombre}.")
              #      return render(request, 'ventas/ventaEditarForm.html', {
               #         'form': form, 
                #        'ventaFormset': formset, 
                 #       'venta': venta, 
                  #      'productos': json.dumps(productos_dict)
                   # })

            # Guardar cambios después de validar stock
            #form.save()
           # formset.instance = venta  

            # Recalcular los subtotales de los productos
            #total_subtotal = 0
            #for detalle in detalles_venta:
            #    producto = detalle.id_producto
            #    producto.stock -= detalle.cantidad
            #    producto.save()
                
                # Calcular el subtotal y guardar
             #   detalle.subtotal = detalle.cantidad * producto.precio_unitario
              #  detalle.precio_unitario = producto.precio_unitario
              #  detalle.save()

               # total_subtotal += detalle.subtotal

            # Actualizar el descuento y el total de la venta
           # descuento = float(request.POST.get('total-descuento', 0))  # Obtener descuento desde el formulario
            #venta.descuento = descuento
            #venta.subtotal = total_subtotal  # Actualizar el subtotal global
            #venta.total = total_subtotal - descuento  # Calcular el total final
            #venta.save()

           # messages.success(request, f'La venta "{venta.id}" se ha actualizado correctamente.')
           # return HttpResponseRedirect(reverse('ventasLista'))
        
        # Si hay errores en el formulario o formset
        print("Errores en el formulario principal: ", form.errors)
        print("Errores en el formset: ", formset.errors)

    else:
        form = ventaForm(instance=venta)
        formset = ventaFormset(instance=venta)

     # Obtenemos los precios de los productos
    productos = Producto.objects.all()  # Obtener todos los productos
    productos_dict = {
                      p["id"]: float(p["precio_unitario"])  # Convertir Decimal a float
                      for p in productos.values("id", "precio_unitario")
                     }
    context = {
        'form': form, 
        'venta': venta, 
        'ventaFormset': formset,
        'productos': json.dumps(productos_dict)  # Serializar a JSON productos_dict  # Pasar productos como JSON
    }

    return render(request, 'ventas/ventaEditarForm.html', context)

#PRODUCTO-----------------------------------------------------------------------

#VISTA BASADA DE CLASE + PAGINACION + FILTRO DE BUSQUEDA--------------------------------/
class ProductosLista(ListView):
    model = Producto
    template_name = "productos/productosLista.html"
    context_object_name = "productos"
    paginate_by = 6

    # Filtro de búsqueda: busca por nombre o descripción
    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(Q(nombre__icontains=query) | Q(descripcion__icontains=query))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')

         # Agregar el total de cada producto (precio_unitario * stock)
        for producto in context['productos']:
            producto.total = (producto.precio_unitario or 0) * (producto.stock or 0)

        # Filtrar productos con bajo stock y pasarlos al contexto
        context['productos_bajo_stock'] = Producto.objects.filter(stock__lt=5)

        return context


#------------------------------------------------------/

def productoDetalle(request, pk):
    producto = Producto.objects.get(pk = pk)
    context = {"producto": producto}
    return render (request, "productos/productoDetalle.html", context)

def productoEliminar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        if not check_write_permission(request):
            return redirect('productosLista')
        
        producto.delete()
        messages.error(request, "Producto eliminado con éxito.")
        return redirect('productosLista')
    return render(request, 'productos/productoEliminar.html', {'producto': producto})

#USANDO FORMS.PY------------------

def productoEditar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == 'POST':
        if not check_write_permission(request):
            form = productoForm(instance=producto)
            return render(request, 'productos/productoEditarForm.html', {'form': form, 'producto': producto})
        
        form = productoForm(request.POST, request.FILES, instance=producto)

        if form.is_valid():
            if form.has_changed():
            # Verificar si se quiere eliminar la imagen
                if form.cleaned_data.get('eliminar_imagen'):
                    if producto.imagen:  # Si existe una imagen
                        ruta_imagen = os.path.join(settings.MEDIA_ROOT, str(producto.imagen))
                        if os.path.exists(ruta_imagen):  # Eliminar archivo físico
                            os.remove(ruta_imagen)
                        producto.imagen = None 

                # Guardar el formulario con los cambios
                form.save()
                messages.success(request, f"El producto '{producto.nombre}' se ha actualizado correctamente.")
            else:
                messages.info(request, "No se han realizado cambios en el producto.")  
            return HttpResponseRedirect(reverse('productosLista'))

        else:
            # Mostrar mensajes de error si el formulario no es válido
            messages.error(request, "Por favor corrige los errores en el formulario.")
    
    else:
        form = productoForm(instance=producto)

    return render(request, 'productos/productoEditarForm.html', {'form': form, 'producto': producto})
    
def productoCrear(request):
    if request.method == 'POST':
        if not check_write_permission(request):
            return render(request, 'productos/productoCrearForm.html', {'form': productoForm()})
        
        form = productoForm(request.POST,  request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto creado con éxito.")
            return HttpResponseRedirect(reverse('productosLista'))
    else:
        form = productoForm()
    return render(request, 'productos/productoCrearForm.html', {'form': form})


#PROVEEDORES-----------------------------------------------------------------------

# def proveedoresLista(request):
#     proveedores = Proveedor.objects.all()  # Obtener todos los proveedores
#     context = {"proveedores": proveedores}  # Pasar los proveedores al contexto
#     return render(request, "proveedores/proveedoresLista.html", context)  # Renderizar el template

#VISTA BASADA DE CLASE + PAGINACION + FILTRO DE BUSQUEDA--------------------------------/
class ProveedoresLista(ListView):
    model = Proveedor
    template_name = "proveedores/proveedoresLista.html"
    context_object_name = "proveedores"
    #paginacion
    paginate_by = 6

    #filtro de busqueda : filtra por titulo y descripcion
    def get_queryset(self): #queryset= conjunto de consultas de ListView 
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(Q(nombre__icontains=query) | Q(direccion__icontains=query))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context

#--------------------------------------------------------------------------------------/
def proveedorDetalle(request, pk):
    proveedor = Proveedor.objects.get(pk=pk)
    compras = Compra.objects.filter(id_proveedor=proveedor)  # Filtrar las compras del proveedor
    context = {
        "proveedor": proveedor,
        "compras": compras,  # Pasar las compras al contexto
    }
    return render(request, "proveedores/proveedorDetalle.html", context)


def proveedorEliminar(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)  # Obtienes el proveedor por su pk

    if request.method == 'POST':
        if not check_write_permission(request):
            return redirect('proveedoresLista')
        
        proveedor.delete()  # Llamas al método delete() sobre la instancia
        messages.error(request, "Proveedor eliminado con éxito.")
        return redirect('proveedoresLista')  # Redirigir a la lista de proveedores

    return render(request, 'proveedores/proveedorEliminar.html', {'proveedor': proveedor})



def proveedorCrear(request):
    next_url = request.GET.get('next')  # Capturamos la URL de retorno si existe

    if request.method == 'POST':
        if not check_write_permission(request):
            return render(request, 'proveedores/proveedorCrear.html')
        
        nombre = request.POST.get('nombre')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')
        email = request.POST.get('email')

        proveedor = Proveedor.objects.create(
            nombre=nombre,
            telefono=telefono,
            direccion=direccion,
            email=email
        )

        messages.success(request, f'Proveedor "{proveedor.nombre}" creado con éxito.')

        # Redirigir según la existencia de 'next'
        return redirect(next_url if next_url else 'proveedoresLista')

    return render(request, 'proveedores/proveedorCrear.html')
    


def proveedorEditar(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)

    if request.method == 'POST':
        if not check_write_permission(request):
            return render(request, 'proveedores/proveedorEditar.html', {'proveedor': proveedor})
        
        # Obtener los datos del formulario
        nuevo_nombre = request.POST.get('nombre').strip()
        nuevo_telefono = request.POST.get('telefono').strip()
        nuevo_direccion = request.POST.get('direccion').strip()
        nuevo_email = request.POST.get('email').strip()

        # Comparar los valores actuales con los nuevos
        cambios_realizados = (
            proveedor.nombre != nuevo_nombre or
            proveedor.telefono != nuevo_telefono or
            proveedor.direccion != nuevo_direccion or
            proveedor.email != nuevo_email
        )

        if cambios_realizados:
            # Si hubo cambios, actualizar el proveedor
            proveedor.nombre = nuevo_nombre
            proveedor.telefono = nuevo_telefono
            proveedor.direccion = nuevo_direccion
            proveedor.email = nuevo_email
            proveedor.save()
            messages.success(request, f'El proveedor "{proveedor.nombre}" se ha actualizado correctamente.')
        else:
            # Si no hubo cambios, mostrar mensaje
            messages.info(request, "No se han realizado cambios en el proveedor.")

        # Redirigir a la lista de proveedores
        return redirect('proveedoresLista')

    # Pasar datos al template
    return render(request, 'proveedores/proveedorEditar.html', {'proveedor': proveedor})
#COMPRA ------------------------------------------------------------

class ComprasLista(ListView):
    model = Compra
    template_name = 'compras/comprasLista.html'
    context_object_name = 'compra'
    paginate_by = 4

    def get_queryset(self):
        queryset = Compra.objects.all().order_by('-fecha')
        
        # Búsqueda por nombre de proveedor
        query = self.request.GET.get('q', '')
        if query:
            queryset = queryset.filter(id_proveedor__nombre__icontains=query)
        
        # Filtrar por estado (anulado o no)
        filtro = self.request.GET.get('filtro', 'no')
        if filtro == 'si':
            queryset = queryset.filter(anulado=True)
        elif filtro == 'no':
            queryset = queryset.filter(anulado=False)

        # Filtrar por fecha
        filtro_fecha = self.request.GET.get('filtro_fecha', '')
        if filtro_fecha == 'ultimos_7':
            hace_siete_dias = datetime.now() - timedelta(days=7)
            queryset = queryset.filter(fecha__gte=hace_siete_dias)

        # Filtrar por mes y año
        filtro_mes = self.request.GET.get('filtro_fecha', 'todas')
        filtro_anio = self.request.GET.get('filtro_anio', str(datetime.now().year))  # Año actual por defecto

        if filtro_mes != 'todas' and filtro_mes.isdigit() and 1 <= int(filtro_mes) <= 12:
            mes = int(filtro_mes)
            año = int(filtro_anio)
            fecha_inicio = make_aware(datetime(año, mes, 1))

            if mes == 12:
                fecha_fin = make_aware(datetime(año + 1, 1, 1))  # Si es diciembre, el siguiente mes es enero del año siguiente
            else:
                fecha_fin = make_aware(datetime(año, mes + 1, 1))  # El primer día del siguiente mes

            queryset = queryset.filter(fecha__gte=fecha_inicio, fecha__lt=fecha_fin)
        elif filtro_anio.isdigit():  # Filtrar solo por año
            año = int(filtro_anio)
            fecha_inicio = make_aware(datetime(año, 1, 1))
            fecha_fin = make_aware(datetime(año + 1, 1, 1))
            queryset = queryset.filter(fecha__gte=fecha_inicio, fecha__lt=fecha_fin)

        # Ordenar por fecha (ascendente o descendente)
        ordenar = self.request.GET.get('ordenar', 'desc')
        if ordenar == 'asc':
            queryset = queryset.order_by('fecha')
        else:
            queryset = queryset.order_by('-fecha')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        meses_nombres = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]

        # Obtener años únicos de compra para el filtro de año
        años_disponibles = Compra.objects.dates('fecha', 'year', order='DESC').values_list('fecha__year', flat=True)

        context.update({
            'filtro': self.request.GET.get('filtro', 'no'),
            'query': self.request.GET.get('q', ''),
            'filtro_fecha': self.request.GET.get('filtro_fecha', 'todas'),
            'filtro_anio': self.request.GET.get('filtro_anio', str(datetime.now().year)),
            'ordenar': self.request.GET.get('ordenar', 'desc'),
            'meses': enumerate(meses_nombres, start=1),  # (1, "Enero"), (2, "Febrero")...
            'años_disponibles': años_disponibles
        })

        # Paginación
        paginator = Paginator(self.get_queryset(), self.paginate_by)
        page = self.request.GET.get('page')

        try:
            context['compra'] = paginator.page(page)
        except PageNotAnInteger:
            # Si no es un número válido, muestra la primera página
            context['compra'] = paginator.page(1)
        except EmptyPage:
            # Si la página es mayor que el número de páginas, redirige a la última página
            context['compra'] = paginator.page(paginator.num_pages)

        # Si no hay compra, agregar un mensaje de "no resultados"
        if not context['compra']:
            context['no_results'] = True


        return context


def compraDetalle(request, pk):
    compra = get_object_or_404(Compra, pk=pk)
    
    # Crear el inline formset para los insumos relacionados con la compra
    formset = compraFormset(instance=compra)
    
    context = {
        'compra': compra,
        'formset': formset,  # Pasamos el formset al contexto
    }
    
    return render(request, 'compras/compraDetalle.html', context)

#FUNCION CON FORMSET--------------
def compraCrear(request):
    
    if request.method == 'POST':
        if not check_write_permission(request):
            form = compraForm()
            formset = compraFormset(queryset=Compra_Insumo.objects.none())
            insumos_iniciales = Compra_Insumo.objects.none()
            return render(request, 'compras/compraCrearForm.html', {
                'form': form, 
                'compraFormset': formset,
                'insumos_iniciales': insumos_iniciales})
        
        form = compraForm(request.POST)
        formset = compraFormset(request.POST)

        if form.is_valid() and formset.is_valid():
            compra = form.save()  # Guarda la compra
            formset.instance = compra  # Asocia el formset con la compra
            detalles_compra = formset.save()  # Guarda los insumos relacionados
            
            # Actualizar el stock de cada insumo comprado 
            for detalle in detalles_compra:
                insumo = detalle.id_insumo  # Obtiene el objeto insumo
                insumo.cantidad += detalle.cantidad  # Suma la cantidad comprada del insumo
                insumo.save()  # Guarda el cambio en el stock

            return HttpResponseRedirect(reverse('comprasLista'))
    else:
        form = compraForm()
        formset = compraFormset(queryset=Compra_Insumo.objects.none())  # Inicializa el formset vacío

    # Obtener insumos según proveedor para la carga inicial
    insumos_iniciales = Compra_Insumo.objects.none()

    return render(request, 'compras/compraCrearForm.html', {
        'form': form, 
        'compraFormset': formset,
        'insumos_iniciales': insumos_iniciales})

def obtener_insumos_por_proveedor(request, proveedor_id):
    insumos = Insumo.objects.filter(id_proveedor=proveedor_id)
    insumos_data = [{'id': insumo.id, 'insumo': insumo.insumo} for insumo in insumos]
    return JsonResponse({'insumos': insumos_data})



#FUNCION PARA AGREGAR LOS CAMPOS FORMSET AL EDITAR ----------------------------------------
def compraEditar(request, pk):
    compra = get_object_or_404(Compra, pk=pk)

    if request.method == 'POST':
        if not check_write_permission(request):
            form = compraForm(instance=compra)
            formset = compraFormset(instance=compra)
            return render(request, 'compras/compraEditarForm.html', {'form': form, 'compra': compra, 'compraFormset': formset})
        
        form = compraForm(request.POST, instance=compra)
        formset = compraFormset(request.POST, instance=compra)

        if form.is_valid() and formset.is_valid():
            if form.has_changed() or any(form.cleaned_data for form in formset.forms if form.has_changed()):
                form.save()
                formset.save()
                messages.success(request, f'La compra "{compra.id}" se ha actualizado correctamente.')
            else:
                messages.info(request, "No se han realizado cambios en la compra.")

            return HttpResponseRedirect(reverse('comprasLista'))
        
        print("Errores en el formulario principal: ", form.errors)
        print("Errores en el formset: ", formset.errors)

    else:
        form = compraForm(instance=compra)
        formset = compraFormset(instance=compra)

    return render(request, 'compras/compraEditarForm.html', {'form': form, 'compra': compra, 'compraFormset': formset})







#INSUMOS----------------------------------------------------------------------------

#VISTA BASADA DE CLASE + PAGINACION + FILTRO DE BUSQUEDA--------/
class InsumosLista(ListView):
    model = Insumo
    template_name = "insumos/insumosLista.html"
    context_object_name = "insumos"
    paginate_by = 6  # Paginación

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.order_by('id')

        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(Q(insumo__icontains=query))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')

        # Obtener la fecha y hora actual
        now = timezone.now()

        # Umbrales de bajo stock según la unidad de medida
        umbrales_bajo_stock = {
            'Gr': 500,
            'Lts': 5,
            'Kg': 1,
            'Ml': 500,
        }

    
         # Filtrar insumos con bajo stock basado en la unidad de medida
        insumos_bajo_stock = []
        for insumo in context['insumos']:
            umbral = umbrales_bajo_stock.get(insumo.unidad_medida, None)  # Obtener umbral según unidad
            if umbral is not None and insumo.cantidad < umbral:
                insumos_bajo_stock.append(insumo)


        # Filtrar insumos con bajo stock
        context['insumos_poca_cantidad'] = insumos_bajo_stock

        # Filtrar insumos vencidos
        context['insumos_vencidos'] = Insumo.objects.filter(fecha_de_vencimiento__lt=now)

        # Filtrar insumos por vencer (dentro de los próximos 7 días)
        context['insumos_por_vencer'] = Insumo.objects.filter(
            fecha_de_vencimiento__gte=now,
            fecha_de_vencimiento__lte=now + timezone.timedelta(days=7)
        )

        return context
#---------------------------------------------------------------/

def insumoDetalle(request, pk):
    insumo= Insumo.objects.get(pk = pk)
    context = {"insumo": insumo}
    return render(request, "insumos/insumoDetalle.html", context)




def insumoCrear(request):
    data = {
        "insumo": request.GET.get("insumo", ""),
        "cantidad": request.GET.get("cantidad", ""),
        "contenido_neto": request.GET.get("contenido_neto", ""),
        "precio": request.GET.get("precio", ""),
        "fecha_de_vencimiento": request.GET.get("fecha_de_vencimiento", ""),
        "id_proveedor": request.GET.get("id_proveedor", None)
    }

    form = insumoForm(initial=data)  # Rellenamos el formulario con los datos recuperados

    if request.method == "POST":
        if not check_write_permission(request):
            return render(request, 'insumos/insumoCrearForm.html', {'form': form})
        
        form = insumoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Insumo creado con éxito.")
            return redirect('insumosLista')

    return render(request, 'insumos/insumoCrearForm.html', {'form': form})


def insumoEditar(request, pk):
    insumo = get_object_or_404(Insumo, pk=pk)
    if request.method == "POST":
        if not check_write_permission(request):
            form = insumoForm(instance=insumo)
            return render(request, 'insumos/insumoEditarForm.html', {'form': form})
        
        form = insumoForm(request.POST, instance=insumo)
        if form.is_valid():
            if form.has_changed():  # Verifica si hubo cambios en el formulario
                form.save()
                messages.success(request, f'El insumo "{insumo.insumo}" se ha actualizado correctamente.')
            else:
                messages.info(request, "No se han realizado cambios en el insumo.")
            return redirect('insumosLista')  # Redirige a la lista de insumos
    else:
        form = insumoForm(instance=insumo)
    
    return render(request, 'insumos/insumoEditarForm.html', {'form': form})


def insumoEliminar(request, pk):
    producto = get_object_or_404(Insumo, pk=pk)
    if request.method == 'POST':
        if not check_write_permission(request):
            return redirect('insumosLista')
        
        producto.delete()
        messages.error(request, "Insumo eliminado con éxito.")
        return redirect('insumosLista')  # Verifica que este nombre coincide con el configurado en urls.py
    return render(request, 'insumos/insumoEliminar.html', {'producto': producto})


#DESTILADOS------------------------------------------------------------------------

#VISTA BASADA DE CLASE + PAGINACION + FILTRO DE BUSQUEDA--------------------------------/
class DestiladosLista(ListView): 
    model = Destilado
    template_name = "destilados/destiladosLista.html"
    context_object_name = "destilados"
    #paginacion
    paginate_by = 6

    #filtro de busqueda : filtra por titulo y descripcion
    def get_queryset(self): #queryset= conjunto de consultas de ListView 
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(Q(nombre__icontains=query))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context


def destiladoCrear(request):
    if request.method == 'POST':
        if not check_write_permission(request):
            return render(request, 'destilados/destiladoCrearForm.html', {'form': destiladoForm()})
        
        form = destiladoForm(request.POST)
        if form.is_valid():
            form.save()  # Guardar el destilado en la base de datos
            messages.success(request, "Destilado creado con éxito.")
            return redirect('destiladosLista')  # Redirige a la lista de destilados
    else:
        form = destiladoForm()
    
    return render(request, 'destilados/destiladoCrearForm.html', {'form': form})

def destiladoEditar(request, pk):
    destilado = get_object_or_404(Destilado, pk=pk)
    
    if request.method == "POST":
        if not check_write_permission(request):
            form = destiladoForm(instance=destilado)
            return render(request, 'destilados/destiladoEditarForm.html', {'form': form, 'destilado': destilado})
        
        if 'eliminar' in request.POST:  # Verifica si se hizo clic en el botón de eliminar
            destilado.delete()
            messages.success(request, f'El destilado "{destilado.nombre}" ha sido eliminado correctamente.')
            return redirect('destiladosLista')  # Redirige a la lista de destilados después de eliminar
        
        form = destiladoForm(request.POST, instance=destilado)
        if form.is_valid():
            if form.has_changed():  # Verifica si hubo cambios en el formulario
                form.save()
                messages.success(request, f'El destilado "{destilado.nombre}" se ha actualizado correctamente.')
            else:
                messages.info(request, "No se han realizado cambios en el destilado.")
            return redirect('destiladosLista')  # Redirige a la lista de destilados después de guardar
    else:
        form = destiladoForm(instance=destilado)
    
    return render(request, 'destilados/destiladoEditarForm.html', {'form': form, 'destilado': destilado})


def destiladoEliminar(request, pk):
    destilado = get_object_or_404(Destilado, pk=pk)
    if request.method == 'POST':
        if not check_write_permission(request):
            return redirect('destiladosLista')
        
        destilado.delete()
        messages.error(request, "Destilado eliminado con éxito.")
        return redirect('destiladosLista')  # Verifica que este nombre coincide con el configurado en urls.py
    return render(request, 'destilados/destiladoEliminar.html', {'destilado': destilado})

from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        
        if form.is_valid():
            user = form.save()
            login(request, user)  # Iniciar sesión automáticamente después del registro
            return redirect("index")  # Redirigir a la página principal o al dashboard
    else:
        form = UserCreationForm()
    
    return render(request, "registration/register.html", {"form": form})

from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy
from django.contrib.auth.forms import PasswordResetForm

class CustomPasswordResetView(PasswordResetView):
    template_name = "registration/passwordReset.html"  # Ruta correcta
    email_template_name = "registration/passwordResetEmail.html"  # Correo
    success_url = reverse_lazy("passwordResetDone")
    form_class = PasswordResetForm
