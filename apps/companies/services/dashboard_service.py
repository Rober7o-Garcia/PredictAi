from django.db.models import Sum, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from typing import Dict, List, Any
import logging
from ..models import Producto, Venta, ItemVenta
from ..models import Compra
from dateutil.relativedelta import relativedelta
from dateutil.relativedelta import relativedelta


logger = logging.getLogger(__name__)


class DashboardService:
    """
    Servicio para gestionar las métricas y datos del dashboard.
    Centraliza la lógica de negocio para evitar duplicación en las vistas.
    """
    
    @staticmethod
    def get_date_ranges() -> Dict[str, timezone.datetime]:
        """Obtiene los rangos de fechas necesarios para las métricas"""
        hoy = timezone.now()
        inicio_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        hace_30_dias = hoy - timedelta(days=30)
        
        return {
            'hoy': hoy,
            'inicio_mes': inicio_mes,
            'hace_30_dias': hace_30_dias
        }
    
    @staticmethod
    def get_ventas_metrics() -> Dict[str, Decimal]:
        """
        Calcula métricas de ventas (hoy y mes)
        
        Returns:
            Dict con ventas_hoy y ventas_mes
        """
        try:
            dates = DashboardService.get_date_ranges()
            
            ventas_hoy = Venta.objects.filter(
                fecha__date=dates['hoy'].date()
            ).aggregate(total=Sum('total'))['total'] or Decimal('0')
            
            ventas_mes = Venta.objects.filter(
                fecha__gte=dates['inicio_mes']
            ).aggregate(total=Sum('total'))['total'] or Decimal('0')
            
            return {
                'ventas_hoy': ventas_hoy,
                'ventas_mes': ventas_mes
            }
        except Exception as e:
            logger.error(f"Error al calcular métricas de ventas: {e}")
            return {
                'ventas_hoy': Decimal('0'),
                'ventas_mes': Decimal('0')
            }
    
    @staticmethod
    def get_ganancia_mes() -> Decimal:
        """
        Calcula la ganancia total del mes actual.
        Usa agregación de Django para mejor performance (no itera en Python).
        
        Returns:
            Ganancia total del mes
        """
        try:
            dates = DashboardService.get_date_ranges()
            
            # OPTIMIZACIÓN: Usar anotaciones de Django en lugar de iterar en Python
            ganancia = ItemVenta.objects.filter(
                venta__fecha__gte=dates['inicio_mes']
            ).aggregate(
                total=Sum(
                    (F('precio_unitario') - F('costo_unitario')) * F('cantidad')
                )
            )['total'] or Decimal('0')
            
            return ganancia
        except Exception as e:
            logger.error(f"Error al calcular ganancia del mes: {e}")
            return Decimal('0')
    
    @staticmethod
    def get_top_productos(limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene los productos más vendidos de los últimos 30 días
        
        Args:
            limit: Número máximo de productos a retornar
            
        Returns:
            Lista de diccionarios con información de productos
        """
        try:
            dates = DashboardService.get_date_ranges()
            
            productos_top = ItemVenta.objects.filter(
                venta__fecha__gte=dates['hace_30_dias']
            ).values('producto__nombre').annotate(
                total=Sum('cantidad'),
                ingresos=Sum('subtotal')
            ).order_by('-total')[:limit]
            
            return list(productos_top)
        except Exception as e:
            logger.error(f"Error al obtener top productos: {e}")
            return []
    
    @staticmethod
    def get_productos_mejor_margen(limit: int = 10):
        """
        Obtiene los productos con mejor margen de ganancia
        
        Args:
            limit: Número máximo de productos a retornar
            
        Returns:
            QuerySet de productos ordenados por margen
        """
        try:
            # Usar anotación para calcular margen en la base de datos
            productos = Producto.objects.filter(
                activo=True
            ).annotate(
                margen=F('precio_venta') - F('precio_compra')
            ).order_by('-margen')[:limit]
            
            return productos
        except Exception as e:
            logger.error(f"Error al obtener productos con mejor margen: {e}")
            return Producto.objects.none()
    
    @staticmethod
    def get_productos_a_reponer():
        """
        Obtiene productos que necesitan reposición
        
        Returns:
            QuerySet de productos con stock bajo
        """
        try:
            productos = Producto.objects.filter(
                stock_actual__lte=F('stock_minimo'),
                activo=True
            ).order_by('stock_actual')
            
            return productos
        except Exception as e:
            logger.error(f"Error al obtener productos a reponer: {e}")
            return Producto.objects.none()
    
    @staticmethod
    def get_ventas_ultimos_dias(dias: int = 7) -> Dict[str, List]:
        """
        Obtiene las ventas de los últimos N días
        
        Args:
            dias: Número de días a retroceder
            
        Returns:
            Dict con labels (fechas) y datos (totales de venta)
        """
        try:
            hoy = timezone.now()
            labels = []
            datos = []
            
            for i in range(dias - 1, -1, -1):
                dia = hoy - timedelta(days=i)
                total = Venta.objects.filter(
                    fecha__date=dia.date()
                ).aggregate(t=Sum('total'))['t'] or Decimal('0')
                
                labels.append(dia.strftime('%d/%m'))
                datos.append(float(total))
            
            return {
                'labels': labels,
                'datos': datos
            }
        except Exception as e:
            logger.error(f"Error al obtener ventas de últimos días: {e}")
            return {
                'labels': [],
                'datos': []
            }
    
    @staticmethod
    def get_dashboard_data() -> Dict[str, Any]:
        """
        Obtiene todos los datos necesarios para el dashboard COMPLETO
        Compatible con dashboard HTML antiguo Y nuevos KPIs
        """
        try:
            # ========================================
            # NUEVOS KPIs (para API y nuevo HTML)
            # ========================================
            liquidez_data = DashboardService.get_liquidez_mes()
            margen_neto = DashboardService.get_margen_neto_porcentaje()
            ticket_promedio = DashboardService.get_ticket_promedio_mes()
            ventas = DashboardService.get_ventas_metrics()
            
            # Datos para gráficos nuevos
            ventas_mensuales = DashboardService.get_ventas_mensuales(6)
            top_productos = DashboardService.get_top_productos(10)
            ventas_categoria = DashboardService.get_ventas_por_categoria()
            flujo_caja = DashboardService.get_flujo_caja_mensual(6)
            
            # ========================================
            # DATOS VIEJOS (para dashboard HTML actual)
            # ========================================
            ganancia_mes = DashboardService.get_ganancia_mes()
            ventas_semana = DashboardService.get_ventas_ultimos_dias(7)
            
            # Productos con mejor margen (SERIALIZAR)
            productos_margen_qs = DashboardService.get_productos_mejor_margen()
            productos_margen_list = []
            for prod in productos_margen_qs:
                productos_margen_list.append({
                    'id': prod.id,
                    'nombre': prod.nombre,
                    'precio_compra': float(prod.precio_compra),
                    'precio_venta': float(prod.precio_venta),
                    'ganancia_unitaria': float(prod.ganancia_unitaria),
                })
            
            # Productos a reponer (SERIALIZAR)
            productos_reponer_qs = DashboardService.get_productos_a_reponer()
            productos_reponer_list = []
            for prod in productos_reponer_qs:
                productos_reponer_list.append({
                    'id': prod.id,
                    'nombre': prod.nombre,
                    'stock_actual': prod.stock_actual,
                    'stock_minimo': prod.stock_minimo,
                    'categoria': prod.categoria.nombre if prod.categoria else None,
                    'proveedor': prod.proveedor.nombre if prod.proveedor else None,
                })
            
            return {
                # ========================================
                # NUEVOS KPIs (para nuevo dashboard)
                # ========================================
                'liquidez': float(liquidez_data['liquidez']),
                'margen_neto_porcentaje': float(margen_neto),
                'ticket_promedio': float(ticket_promedio),
                'ventas_mes': float(ventas['ventas_mes']),
                
                # Gráficos nuevos
                'labels_meses': ventas_mensuales['labels'],
                'datos_meses': ventas_mensuales['datos'],
                'labels_productos': [p['producto__nombre'] for p in top_productos],
                'datos_productos': [float(p['ingresos']) for p in top_productos],
                'labels_categorias': [c['producto__categoria__nombre'] for c in ventas_categoria],
                'datos_categorias': [float(c['total']) for c in ventas_categoria],
                'labels_flujo': flujo_caja['labels'],
                'datos_ingresos': flujo_caja['ingresos'],
                'datos_egresos': flujo_caja['egresos'],
                
                # ========================================
                # DATOS VIEJOS (compatibilidad)
                # ========================================
                'ventas_hoy': float(ventas['ventas_hoy']),
                'ganancia_mes': float(ganancia_mes),
                'productos_top': top_productos,
                'productos_margen': productos_margen_list,  # ✅ SERIALIZADO
                'labels_semana': ventas_semana['labels'],
                'datos_semana': ventas_semana['datos'],
                
                # ========================================
                # PRODUCTOS A REPONER (serializado)
                # ========================================
                'productos_reponer': productos_reponer_list,
                'productos_reponer_count': len(productos_reponer_list),
            }
        except Exception as e:
            logger.error(f"Error al obtener datos del dashboard: {e}")
            return {}        
            
    @staticmethod
    def get_liquidez_mes() -> Dict[str, Decimal]:
        """
        Calcula la liquidez del mes (Ventas - Compras)
        """
        
        try:
            dates = DashboardService.get_date_ranges()
            
            ingresos = Venta.objects.filter(
                fecha__gte=dates['inicio_mes']
            ).aggregate(total=Sum('total'))['total'] or Decimal('0')
            
            egresos = Compra.objects.filter(
                fecha__gte=dates['inicio_mes']
            ).aggregate(total=Sum('total'))['total'] or Decimal('0')
            
            liquidez = ingresos - egresos
            
            return {
                'liquidez': liquidez,
                'ingresos': ingresos,
                'egresos': egresos
            }
        except Exception as e:
            logger.error(f"Error al calcular liquidez: {e}")
            return {
                'liquidez': Decimal('0'),
                'ingresos': Decimal('0'),
                'egresos': Decimal('0')
            }

    @staticmethod
    def get_ticket_promedio_mes() -> Decimal:
        """
        Calcula el ticket promedio del mes (Total ventas / # transacciones)
        """
        try:
            dates = DashboardService.get_date_ranges()
            
            ventas = Venta.objects.filter(fecha__gte=dates['inicio_mes'])
            total = ventas.aggregate(t=Sum('total'))['t'] or Decimal('0')
            cantidad = ventas.count()
            
            if cantidad > 0:
                return total / cantidad
            return Decimal('0')
        except Exception as e:
            logger.error(f"Error al calcular ticket promedio: {e}")
            return Decimal('0')

    @staticmethod
    def get_margen_neto_porcentaje() -> Decimal:
        """
        Calcula el margen de utilidad neta en porcentaje
        (Ganancia / Ventas Totales) * 100
        """
        try:
            dates = DashboardService.get_date_ranges()
            
            ventas_total = Venta.objects.filter(
                fecha__gte=dates['inicio_mes']
            ).aggregate(t=Sum('total'))['t'] or Decimal('0')
            
            ganancia = ItemVenta.objects.filter(
                venta__fecha__gte=dates['inicio_mes']
            ).aggregate(
                total=Sum((F('precio_unitario') - F('costo_unitario')) * F('cantidad'))
            )['total'] or Decimal('0')
            
            if ventas_total > 0:
                return (ganancia / ventas_total) * 100
            return Decimal('0')
        except Exception as e:
            logger.error(f"Error al calcular margen neto: {e}")
            return Decimal('0')

    @staticmethod
    def get_ventas_por_categoria() -> List[Dict[str, Any]]:
        """
        Obtiene ventas agrupadas por categoría (para gráfico circular)
        """
        try:
            dates = DashboardService.get_date_ranges()
            
            categorias = ItemVenta.objects.filter(
                venta__fecha__gte=dates['inicio_mes']
            ).values(
                'producto__categoria__nombre'
            ).annotate(
                total=Sum('subtotal')
            ).order_by('-total')
            
            return list(categorias)
        except Exception as e:
            logger.error(f"Error al obtener ventas por categoría: {e}")
            return []

    @staticmethod
    def get_ventas_mensuales(meses: int = 6) -> Dict[str, List]:
        """
        Obtiene ventas de los últimos N meses
        """
        try:
            
            hoy = timezone.now()
            labels = []
            datos_ventas = []
            
            for i in range(meses - 1, -1, -1):
                mes = hoy - relativedelta(months=i)
                inicio_mes = mes.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                
                if i == 0:
                    fin_mes = hoy
                else:
                    fin_mes = (mes + relativedelta(months=1)).replace(day=1) - timedelta(seconds=1)
                
                total = Venta.objects.filter(
                    fecha__range=[inicio_mes, fin_mes]
                ).aggregate(t=Sum('total'))['t'] or Decimal('0')
                
                labels.append(mes.strftime('%b %Y'))
                datos_ventas.append(float(total))
            
            return {
                'labels': labels,
                'datos': datos_ventas
            }
        except Exception as e:
            logger.error(f"Error al obtener ventas mensuales: {e}")
            return {
                'labels': [],
                'datos': []
            }

    @staticmethod
    def get_flujo_caja_mensual(meses: int = 6) -> Dict[str, List]:
        """
        Obtiene flujo de caja (ingresos vs egresos) de los últimos N meses
        """
        
        try:
            hoy = timezone.now()
            labels = []
            ingresos = []
            egresos = []
            
            for i in range(meses - 1, -1, -1):
                mes = hoy - relativedelta(months=i)
                inicio_mes = mes.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                
                if i == 0:
                    fin_mes = hoy
                else:
                    fin_mes = (mes + relativedelta(months=1)).replace(day=1) - timedelta(seconds=1)
                
                total_ingresos = Venta.objects.filter(
                    fecha__range=[inicio_mes, fin_mes]
                ).aggregate(t=Sum('total'))['t'] or Decimal('0')
                
                total_egresos = Compra.objects.filter(
                    fecha__range=[inicio_mes, fin_mes]
                ).aggregate(t=Sum('total'))['t'] or Decimal('0')
                
                labels.append(mes.strftime('%b'))
                ingresos.append(float(total_ingresos))
                egresos.append(float(total_egresos))
            
            return {
                'labels': labels,
                'ingresos': ingresos,
                'egresos': egresos
            }
        except Exception as e:
            logger.error(f"Error al obtener flujo de caja: {e}")
            return {
                'labels': [],
                'ingresos': [],
                'egresos': []
            }
