# gameplay/services/pattern_analyzer.py
from apps.companies.models import Producto, Venta, ItemVenta
from apps.gameplay.models import InsightNegocio
from django.db.models import Sum, Count, Avg, F, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


def analizar_tendencias_productos():
    """
    Detecta productos con tendencias alcistas o bajistas
    """
    insights = []
    hoy = timezone.now().date()
    hace_30_dias = hoy - timedelta(days=30)
    hace_60_dias = hoy - timedelta(days=60)
    
    productos = Producto.objects.filter(activo=True)
    
    for producto in productos:
        # Ventas últimos 30 días
        ventas_recientes = ItemVenta.objects.filter(
            producto=producto,
            venta__fecha__date__gte=hace_30_dias
        ).aggregate(total=Sum('cantidad'))['total'] or 0
        
        # Ventas 30-60 días atrás
        ventas_anteriores = ItemVenta.objects.filter(
            producto=producto,
            venta__fecha__date__gte=hace_60_dias,
            venta__fecha__date__lt=hace_30_dias
        ).aggregate(total=Sum('cantidad'))['total'] or 0
        
        # Calcular cambio porcentual
        if ventas_anteriores > 0:
            cambio = ((ventas_recientes - ventas_anteriores) / ventas_anteriores) * 100
            
            # Tendencia bajista significativa (>20% de caída)
            if cambio < -20 and ventas_recientes > 0:
                insights.append({
                    'tipo': 'tendencia_baja',
                    'severidad': 'alta' if cambio < -40 else 'media',
                    'titulo': f"⚠️ Caída en ventas de {producto.nombre}",
                    'descripcion': f"Las ventas de '{producto.nombre}' bajaron {abs(cambio):.1f}% en los últimos 30 días. Ventas actuales: {ventas_recientes} unidades vs {ventas_anteriores} unidades el mes anterior.",
                    'recomendacion': f"Considera implementar una promoción o revisar el precio actual (${producto.precio_venta}). También verifica si hay problemas de stock o competencia.",
                    'producto_relacionado': producto.nombre,
                    'metrica_valor': cambio
                })
            
            # Tendencia alcista significativa (>30% de aumento)
            elif cambio > 30:
                insights.append({
                    'tipo': 'tendencia_alza',
                    'severidad': 'alta',
                    'titulo': f"📈 Crecimiento en {producto.nombre}",
                    'descripcion': f"¡Excelente! Las ventas de '{producto.nombre}' aumentaron {cambio:.1f}% en los últimos 30 días. Ventas actuales: {ventas_recientes} unidades vs {ventas_anteriores} unidades.",
                    'recomendacion': f"Aprovecha el momentum: aumenta el stock en {int(cambio/2)}% y considera posicionarlo más visiblemente. Stock actual: {producto.stock_actual} unidades.",
                    'producto_relacionado': producto.nombre,
                    'metrica_valor': cambio
                })
    
    return insights


def detectar_correlaciones():
    """
    Detecta productos que se venden frecuentemente juntos
    """
    insights = []
    
    # Obtener ventas con múltiples items
    ventas_multiples = Venta.objects.annotate(
        num_items=Count('items')
    ).filter(num_items__gte=2)
    
    # Analizar combinaciones comunes
    productos = Producto.objects.filter(activo=True)[:20]  # Limitar para performance
    
    for producto in productos:
        # Ventas que incluyen este producto
        ventas_con_producto = Venta.objects.filter(
            items__producto=producto
        ).distinct()
        
        total_ventas_producto = ventas_con_producto.count()
        
        if total_ventas_producto < 5:  # Mínimo 5 ventas para detectar patrón
            continue
        
        # Buscar otros productos vendidos en las mismas ventas
        otros_productos = ItemVenta.objects.filter(
            venta__in=ventas_con_producto
        ).exclude(
            producto=producto
        ).values('producto__nombre').annotate(
            frecuencia=Count('venta', distinct=True)
        ).order_by('-frecuencia')[:3]
        
        for otro in otros_productos:
            porcentaje = (otro['frecuencia'] / total_ventas_producto) * 100
            
            if porcentaje > 50:  # Se venden juntos más del 50% de las veces
                insights.append({
                    'tipo': 'correlacion',
                    'severidad': 'alta' if porcentaje > 70 else 'media',
                    'titulo': f"💡 Combo Potencial: {producto.nombre} + {otro['producto__nombre']}",
                    'descripcion': f"Detecté que {porcentaje:.0f}% de las veces que vendes '{producto.nombre}', también vendes '{otro['producto__nombre']}'.",
                    'recomendacion': f"Crea un combo o bundle con estos productos. Esto puede aumentar tu ticket promedio y facilitar la decisión de compra.",
                    'producto_relacionado': f"{producto.nombre}, {otro['producto__nombre']}",
                    'metrica_valor': porcentaje
                })
    
    return insights


def detectar_stock_critico():
    """
    Detecta productos con stock crítico basándose en velocidad de venta
    """
    insights = []
    hoy = timezone.now().date()
    hace_30_dias = hoy - timedelta(days=30)
    
    productos = Producto.objects.filter(activo=True, stock_actual__gt=0)
    
    for producto in productos:
        # Calcular ventas diarias promedio
        ventas_mes = ItemVenta.objects.filter(
            producto=producto,
            venta__fecha__date__gte=hace_30_dias
        ).aggregate(total=Sum('cantidad'))['total'] or 0
        
        if ventas_mes == 0:
            continue
        
        promedio_diario = ventas_mes / 30
        
        if promedio_diario > 0:
            # Días de inventario restante
            dias_restantes = producto.stock_actual / promedio_diario
            
            if dias_restantes < 7:  # Menos de una semana de stock
                insights.append({
                    'tipo': 'alerta',
                    'severidad': 'critica' if dias_restantes < 3 else 'alta',
                    'titulo': f"🚨 Stock Crítico: {producto.nombre}",
                    'descripcion': f"'{producto.nombre}' solo tiene {producto.stock_actual} unidades. A tu ritmo actual de ventas ({promedio_diario:.1f} unidades/día), te quedarás sin stock en {dias_restantes:.0f} días.",
                    'recomendacion': f"URGENTE: Ordena al menos {int(promedio_diario * 30)} unidades para cubrir el próximo mes.",
                    'producto_relacionado': producto.nombre,
                    'metrica_valor': dias_restantes
                })
    
    return insights


def detectar_productos_estancados():
    """
    Detecta productos con muy pocas o ninguna venta
    """
    insights = []
    hoy = timezone.now().date()
    hace_60_dias = hoy - timedelta(days=60)
    
    productos = Producto.objects.filter(activo=True)
    
    for producto in productos:
        ventas_60_dias = ItemVenta.objects.filter(
            producto=producto,
            venta__fecha__date__gte=hace_60_dias
        ).aggregate(total=Sum('cantidad'))['total'] or 0
        
        if ventas_60_dias == 0 and producto.stock_actual > 0:
            insights.append({
                'tipo': 'alerta',
                'severidad': 'media',
                'titulo': f"📦 Producto sin ventas: {producto.nombre}",
                'descripcion': f"'{producto.nombre}' no ha tenido ventas en los últimos 60 días. Stock actual: {producto.stock_actual} unidades.",
                'recomendacion': f"Considera: 1) Hacer una promoción agresiva (descuento 20-30%), 2) Reubicarlo en un lugar más visible, o 3) Evaluar si vale la pena seguir vendiéndolo.",
                'producto_relacionado': producto.nombre,
                'metrica_valor': 0
            })
        elif ventas_60_dias < 3 and producto.stock_actual > 10:
            insights.append({
                'tipo': 'oportunidad',
                'severidad': 'media',
                'titulo': f"🐌 Rotación lenta: {producto.nombre}",
                'descripcion': f"'{producto.nombre}' solo vendió {ventas_60_dias} unidades en 60 días, pero tienes {producto.stock_actual} en stock.",
                'recomendacion': f"Reduce pedidos futuros de este producto y considera promociones para acelerar la rotación.",
                'producto_relacionado': producto.nombre,
                'metrica_valor': ventas_60_dias
            })
    
    return insights


def ejecutar_analisis_completo():
    """
    Ejecuta todos los análisis y guarda insights nuevos
    """
    print("🔍 Iniciando análisis de patrones...")
    
    # Recopilar todos los insights
    todos_insights = []
    todos_insights.extend(analizar_tendencias_productos())
    todos_insights.extend(detectar_correlaciones())
    todos_insights.extend(detectar_stock_critico())
    todos_insights.extend(detectar_productos_estancados())
    
    # Guardar en la base de datos
    nuevos_guardados = 0
    for insight_data in todos_insights:
        # Evitar duplicados recientes (mismo título en últimas 48 horas)
        similar_reciente = InsightNegocio.objects.filter(
            titulo=insight_data['titulo'],
            detectado_en__gte=timezone.now() - timedelta(hours=48)
        ).exists()
        
        if not similar_reciente:
            InsightNegocio.objects.create(**insight_data)
            nuevos_guardados += 1
    
    print(f"✅ Análisis completado. {nuevos_guardados} nuevos insights detectados.")
    
    return {
        'total_analizados': len(todos_insights),
        'nuevos_guardados': nuevos_guardados
    }


def obtener_insights_no_vistos():
    """
    Obtiene insights que el usuario aún no ha visto
    """
    return InsightNegocio.objects.filter(visto=False, activo=True).order_by('-severidad', '-detectado_en')


def marcar_insights_como_vistos(ids):
    """
    Marca insights como vistos
    """
    InsightNegocio.objects.filter(id__in=ids).update(visto=True)