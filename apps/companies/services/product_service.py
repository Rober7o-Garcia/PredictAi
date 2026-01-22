from django.db.models import Q, F
from decimal import Decimal
from typing import List, Optional
import logging

from ..models import Producto, Categoria, Proveedor

logger = logging.getLogger(__name__)


class ProductService:
    """
    Servicio para gestionar operaciones relacionadas con productos
    """
    
    @staticmethod
    def get_productos_activos():
        """Obtiene todos los productos activos"""
        try:
            return Producto.objects.filter(activo=True).select_related(
                'categoria', 'proveedor'
            )
        except Exception as e:
            logger.error(f"Error al obtener productos activos: {e}")
            return Producto.objects.none()
    
    @staticmethod
    def get_producto_by_id(producto_id: int) -> Optional[Producto]:
        """
        Obtiene un producto por su ID
        
        Args:
            producto_id: ID del producto
            
        Returns:
            Producto o None si no existe
        """
        try:
            return Producto.objects.select_related(
                'categoria', 'proveedor'
            ).get(id=producto_id, activo=True)
        except Producto.DoesNotExist:
            logger.warning(f"Producto con ID {producto_id} no encontrado")
            return None
        except Exception as e:
            logger.error(f"Error al obtener producto {producto_id}: {e}")
            return None
    
    @staticmethod
    def buscar_productos(query: str):
        """
        Busca productos por nombre o código de barras
        
        Args:
            query: Texto a buscar
            
        Returns:
            QuerySet de productos que coinciden
        """
        try:
            return Producto.objects.filter(
                Q(nombre__icontains=query) | 
                Q(codigo_barras__icontains=query),
                activo=True
            ).select_related('categoria', 'proveedor')
        except Exception as e:
            logger.error(f"Error al buscar productos: {e}")
            return Producto.objects.none()
    
    @staticmethod
    def get_productos_por_categoria(categoria_id: int):
        """Obtiene productos de una categoría específica"""
        try:
            return Producto.objects.filter(
                categoria_id=categoria_id,
                activo=True
            ).select_related('categoria', 'proveedor')
        except Exception as e:
            logger.error(f"Error al obtener productos por categoría: {e}")
            return Producto.objects.none()
    
    @staticmethod
    def get_productos_bajo_stock():
        """Obtiene productos con stock bajo o agotado"""
        try:
            return Producto.objects.filter(
                Q(stock_actual__lte=F('stock_minimo')) | Q(stock_actual=0),
                activo=True
            ).select_related('categoria', 'proveedor').order_by('stock_actual')
        except Exception as e:
            logger.error(f"Error al obtener productos con stock bajo: {e}")
            return Producto.objects.none()
    
    @staticmethod
    def actualizar_stock(producto_id: int, cantidad: int, operacion: str = 'add') -> bool:
        """
        Actualiza el stock de un producto
        
        Args:
            producto_id: ID del producto
            cantidad: Cantidad a agregar o restar
            operacion: 'add' para agregar, 'subtract' para restar
            
        Returns:
            True si la operación fue exitosa, False en caso contrario
        """
        try:
            producto = Producto.objects.get(id=producto_id)
            
            if operacion == 'add':
                producto.stock_actual += cantidad
            elif operacion == 'subtract':
                if producto.stock_actual >= cantidad:
                    producto.stock_actual -= cantidad
                else:
                    logger.warning(f"Stock insuficiente para producto {producto_id}")
                    return False
            
            producto.save()
            logger.info(f"Stock actualizado para producto {producto_id}: {operacion} {cantidad}")
            return True
        except Producto.DoesNotExist:
            logger.error(f"Producto {producto_id} no encontrado")
            return False
        except Exception as e:
            logger.error(f"Error al actualizar stock: {e}")
            return False
    
    @staticmethod
    def calcular_valor_inventario() -> Decimal:
        """
        Calcula el valor total del inventario
        (stock_actual * precio_compra) de todos los productos
        """
        try:
            productos = Producto.objects.filter(activo=True)
            total = sum(
                p.stock_actual * p.precio_compra 
                for p in productos
            )
            return Decimal(str(total))
        except Exception as e:
            logger.error(f"Error al calcular valor de inventario: {e}")
            return Decimal('0')
    
    @staticmethod
    def get_estadisticas_productos():
        """Obtiene estadísticas generales de productos"""
        try:
            total_productos = Producto.objects.filter(activo=True).count()
            productos_agotados = Producto.objects.filter(
                stock_actual=0, 
                activo=True
            ).count()
            productos_bajo_stock = Producto.objects.filter(
                stock_actual__lte=F('stock_minimo'),
                stock_actual__gt=0,
                activo=True
            ).count()
            
            return {
                'total_productos': total_productos,
                'productos_agotados': productos_agotados,
                'productos_bajo_stock': productos_bajo_stock,
                'valor_inventario': ProductService.calcular_valor_inventario()
            }
        except Exception as e:
            logger.error(f"Error al obtener estadísticas de productos: {e}")
            return {
                'total_productos': 0,
                'productos_agotados': 0,
                'productos_bajo_stock': 0,
                'valor_inventario': Decimal('0')
            }