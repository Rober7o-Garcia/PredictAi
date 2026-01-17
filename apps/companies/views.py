from django.shortcuts import render
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta
import json
from .models import Producto, Venta, ItemVenta
from django.http import JsonResponse


def dashboard(request):
    hoy = timezone.now()
    inicio_mes = hoy.replace(day=1)
    hace_30_dias = hoy - timedelta(days=30)
    
    # Ventas
    ventas_hoy = Venta.objects.filter(fecha__date=hoy.date()).aggregate(total=Sum('total'))['total'] or 0
    ventas_mes = Venta.objects.filter(fecha__gte=inicio_mes).aggregate(total=Sum('total'))['total'] or 0
    
    # Ganancia del mes
    items_mes = ItemVenta.objects.filter(venta__fecha__gte=inicio_mes)
    ganancia_mes = sum((item.precio_unitario - item.costo_unitario) * item.cantidad for item in items_mes)
    
    # Top 10 productos más vendidos
    productos_top = ItemVenta.objects.filter(
        venta__fecha__gte=hace_30_dias
    ).values('producto__nombre').annotate(
        total=Sum('cantidad'),
        ingresos=Sum('subtotal')
    ).order_by('-total')[:10]
    
    # Productos con mejor margen
    productos_margen = Producto.objects.filter(activo=True).extra(
        select={'margen': 'precio_venta - precio_compra'}
    ).order_by('-margen')[:10]
    
    # Productos a reponer
    productos_reponer = Producto.objects.filter(
        stock_actual__lte=F('stock_minimo'),
        activo=True
    ).order_by('stock_actual')
    
    # Ventas últimos 7 días
    ventas_semana = []
    labels_semana = []
    datos_semana = []
    
    for i in range(6, -1, -1):
        dia = hoy - timedelta(days=i)
        total = Venta.objects.filter(fecha__date=dia.date()).aggregate(t=Sum('total'))['t'] or 0
        
        labels_semana.append(dia.strftime('%d/%m'))
        datos_semana.append(float(total))
        ventas_semana.append({'fecha': dia.strftime('%d/%m'), 'total': float(total)})
    
    context = {
        'ventas_hoy': ventas_hoy,
        'ventas_mes': ventas_mes,
        'ganancia_mes': ganancia_mes,
        'productos_top': productos_top,
        'productos_margen': productos_margen,
        'productos_reponer': productos_reponer,
        'ventas_semana': ventas_semana,
        'labels_semana': json.dumps(labels_semana),
        'datos_semana': json.dumps(datos_semana),
    }
    return render(request, 'dashboard.html', context)

def dashboard_data(request):
    """API endpoint que devuelve los datos del dashboard en JSON"""
    hoy = timezone.now()
    inicio_mes = hoy.replace(day=1)
    hace_30_dias = hoy - timedelta(days=30)
    
    # Ventas
    ventas_hoy = Venta.objects.filter(fecha__date=hoy.date()).aggregate(total=Sum('total'))['total'] or 0
    ventas_mes = Venta.objects.filter(fecha__gte=inicio_mes).aggregate(total=Sum('total'))['total'] or 0
    
    # Ganancia del mes
    items_mes = ItemVenta.objects.filter(venta__fecha__gte=inicio_mes)
    ganancia_mes = sum((item.precio_unitario - item.costo_unitario) * item.cantidad for item in items_mes)
    
    # Top 10 productos más vendidos
    productos_top = list(ItemVenta.objects.filter(
        venta__fecha__gte=hace_30_dias
    ).values('producto__nombre').annotate(
        total=Sum('cantidad'),
        ingresos=Sum('subtotal')
    ).order_by('-total')[:10])
    
    # Productos a reponer
    productos_reponer = list(Producto.objects.filter(
        stock_actual__lte=F('stock_minimo'),
        activo=True
    ).values('nombre', 'stock_actual', 'stock_minimo').order_by('stock_actual'))
    
    # Ventas últimos 7 días
    labels_semana = []
    datos_semana = []
    
    for i in range(6, -1, -1):
        dia = hoy - timedelta(days=i)
        total = Venta.objects.filter(fecha__date=dia.date()).aggregate(t=Sum('total'))['t'] or 0
        labels_semana.append(dia.strftime('%d/%m'))
        datos_semana.append(float(total))
    
    data = {
        'ventas_hoy': float(ventas_hoy),
        'ventas_mes': float(ventas_mes),
        'ganancia_mes': float(ganancia_mes),
        'productos_reponer_count': len(productos_reponer),
        'productos_top': productos_top,
        'productos_reponer': productos_reponer,
        'labels_semana': labels_semana,
        'datos_semana': datos_semana,
    }
    
    return JsonResponse(data)