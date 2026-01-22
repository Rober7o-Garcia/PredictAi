"""
Sales Service
Maneja la lógica de negocio relacionada con ventas
"""

from django.db import transaction
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
import logging

from ..models import Venta, ItemVenta, Producto
from .firebase_service import FirebaseService  # ← NUEVO IMPORT

logger = logging.getLogger(__name__)


class SalesService:
    """
    Servicio para gestionar operaciones relacionadas con ventas
    """
    
    @staticmethod
    @transaction.atomic
    def crear_venta(items_data: List[Dict], cliente_nombre: str = None, notas: str = None) -> Optional[Venta]:
        """
        Crea una nueva venta con sus items y notifica a Firebase
        
        Args:
            items_data: Lista de dicts con {producto_id, cantidad}
            cliente_nombre: Nombre del cliente (opcional)
            notas: Notas adicionales (opcional)
            
        Returns:
            Venta creada o None si hay error
        """
        try:
            # Crear la venta
            venta = Venta.objects.create(
                cliente_nombre=cliente_nombre,
                notas=notas
            )
            
            # Crear items y actualizar stock
            for item_data in items_data:
                producto = Producto.objects.select_for_update().get(
                    id=item_data['producto_id']
                )
                
                # Verificar stock disponible
                cantidad = item_data['cantidad']
                if producto.stock_actual < cantidad:
                    raise ValueError(f"Stock insuficiente para {producto.nombre}. Disponible: {producto.stock_actual}, Solicitado: {cantidad}")
                
                # Crear item de venta
                ItemVenta.objects.create(
                    venta=venta,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=producto.precio_venta,
                    costo_unitario=producto.precio_compra,
                    subtotal=producto.precio_venta * cantidad
                )
                
                # Actualizar stock
                producto.stock_actual -= cantidad
                producto.save()
            
            # Calcular total de la venta
            venta.calcular_total()
            
            # 🔥 NOTIFICAR A FIREBASE EN TIEMPO REAL
            firebase_success = FirebaseService.ping_update(company_id='demo_company')
            
            if firebase_success:
                logger.info(f"✅ Venta {venta.id} creada (${venta.total}) y notificada a Firebase")
            else:
                logger.warning(f"⚠️ Venta {venta.id} creada pero Firebase no respondió")
            
            return venta
            
        except ValueError as ve:
            logger.warning(f"Error de validación al crear venta: {ve}")
            raise
        except Producto.DoesNotExist:
            logger.error(f"Producto no encontrado: {item_data.get('producto_id')}")
            raise ValueError("Producto no encontrado")
        except Exception as e:
            logger.error(f"Error inesperado al crear venta: {e}")
            raise
    
    @staticmethod
    def get_venta_by_id(venta_id: int) -> Optional[Venta]:
        """Obtiene una venta por su ID con sus items"""
        try:
            return Venta.objects.prefetch_related('items__producto').get(id=venta_id)
        except Venta.DoesNotExist:
            logger.warning(f"Venta {venta_id} no encontrada")
            return None
        except Exception as e:
            logger.error(f"Error al obtener venta: {e}")
            return None
    
    @staticmethod
    def get_ventas_por_fecha(fecha_inicio, fecha_fin=None):
        """Obtiene ventas en un rango de fechas"""
        try:
            if fecha_fin is None:
                fecha_fin = timezone.now()
            
            return Venta.objects.filter(
                fecha__range=[fecha_inicio, fecha_fin]
            ).prefetch_related('items__producto').order_by('-fecha')
        except Exception as e:
            logger.error(f"Error al obtener ventas por fecha: {e}")
            return Venta.objects.none()
    
    @staticmethod
    def get_ventas_del_dia():
        """Obtiene todas las ventas del día actual"""
        try:
            hoy = timezone.now()
            return Venta.objects.filter(
                fecha__date=hoy.date()
            ).prefetch_related('items__producto').order_by('-fecha')
        except Exception as e:
            logger.error(f"Error al obtener ventas del día: {e}")
            return Venta.objects.none()
    
    @staticmethod
    def calcular_ganancia_venta(venta_id: int) -> Decimal:
        """Calcula la ganancia de una venta específica"""
        try:
            items = ItemVenta.objects.filter(venta_id=venta_id)
            ganancia = sum(
                (item.precio_unitario - item.costo_unitario) * item.cantidad 
                for item in items
            )
            return Decimal(str(ganancia))
        except Exception as e:
            logger.error(f"Error al calcular ganancia de venta: {e}")
            return Decimal('0')
    
    @staticmethod
    def get_estadisticas_ventas(dias: int = 30) -> Dict[str, Any]:
        """
        Obtiene estadísticas de ventas de los últimos N días
        
        Args:
            dias: Número de días a analizar
            
        Returns:
            Dict con estadísticas
        """
        try:
            fecha_inicio = timezone.now() - timedelta(days=dias)
            
            ventas = Venta.objects.filter(fecha__gte=fecha_inicio)
            
            total_ventas = ventas.aggregate(total=Sum('total'))['total'] or Decimal('0')
            cantidad_ventas = ventas.count()
            promedio_venta = total_ventas / cantidad_ventas if cantidad_ventas > 0 else Decimal('0')
            
            # Calcular ganancia
            items = ItemVenta.objects.filter(venta__fecha__gte=fecha_inicio)
            ganancia = sum(
                (item.precio_unitario - item.costo_unitario) * item.cantidad 
                for item in items
            )
            
            return {
                'total_ventas': float(total_ventas),
                'cantidad_ventas': cantidad_ventas,
                'promedio_venta': float(promedio_venta),
                'ganancia_total': float(ganancia),
                'margen_promedio': float((ganancia / total_ventas * 100) if total_ventas > 0 else 0)
            }
        except Exception as e:
            logger.error(f"Error al obtener estadísticas de ventas: {e}")
            return {
                'total_ventas': 0.0,
                'cantidad_ventas': 0,
                'promedio_venta': 0.0,
                'ganancia_total': 0.0,
                'margen_promedio': 0.0
            }
    
    @staticmethod
    def get_productos_mas_vendidos(limit: int = 10, dias: int = 30):
        """Obtiene los productos más vendidos en un período"""
        try:
            fecha_inicio = timezone.now() - timedelta(days=dias)
            
            productos = ItemVenta.objects.filter(
                venta__fecha__gte=fecha_inicio
            ).values(
                'producto__id',
                'producto__nombre'
            ).annotate(
                total_vendido=Sum('cantidad'),
                total_ingresos=Sum('subtotal')
            ).order_by('-total_vendido')[:limit]
            
            return list(productos)
        except Exception as e:
            logger.error(f"Error al obtener productos más vendidos: {e}")
            return []