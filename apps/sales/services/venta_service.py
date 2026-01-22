from django.db import transaction
from apps.companies.models import Producto, Venta, ItemVenta
from apps.companies.services import FirebaseService
import logging

logger = logging.getLogger(__name__)

class VentaService:
    """
    Servicio para gestionar ventas desde el punto de venta
    """
    
    @staticmethod
    def buscar_producto_por_codigo(codigo_barras):
        """
        Buscar producto por código de barras
        Implementa búsqueda flexible para cámaras de baja calidad
        """
        try:
            # Limpiar código (quitar espacios, caracteres raros)
            codigo_limpio = codigo_barras.strip().replace(" ", "").replace("-", "")
            
            # Búsqueda exacta
            try:
                producto = Producto.objects.get(codigo_barras=codigo_limpio)
                return {
                    'encontrado': True,
                    'producto': {
                        'id': producto.id,
                        'nombre': producto.nombre,
                        'codigo_barras': producto.codigo_barras,
                        'precio_venta': float(producto.precio_venta),
                        'stock': producto.stock,
                        'categoria': producto.categoria.nombre if producto.categoria else 'Sin categoría'
                    }
                }
            except Producto.DoesNotExist:
                pass
            
            # Búsqueda parcial (últimos 8 dígitos para EAN-13 mal leídos)
            if len(codigo_limpio) >= 8:
                productos = Producto.objects.filter(
                    codigo_barras__icontains=codigo_limpio[-8:]
                )[:5]
                
                if productos.exists():
                    if productos.count() == 1:
                        producto = productos.first()
                        return {
                            'encontrado': True,
                            'producto': {
                                'id': producto.id,
                                'nombre': producto.nombre,
                                'codigo_barras': producto.codigo_barras,
                                'precio_venta': float(producto.precio_venta),
                                'stock': producto.stock,
                                'categoria': producto.categoria.nombre if producto.categoria else 'Sin categoría'
                            },
                            'advertencia': 'Código parcialmente coincidente'
                        }
                    else:
                        return {
                            'encontrado': False,
                            'multiples': True,
                            'productos': [
                                {
                                    'id': p.id,
                                    'nombre': p.nombre,
                                    'codigo_barras': p.codigo_barras,
                                    'precio_venta': float(p.precio_venta)
                                } for p in productos
                            ],
                            'mensaje': 'Se encontraron múltiples productos'
                        }
            
            return {
                'encontrado': False,
                'mensaje': f'No se encontró producto con código: {codigo_barras}'
            }
            
        except Exception as e:
            logger.error(f"Error buscando producto: {e}")
            return {
                'encontrado': False,
                'mensaje': 'Error en la búsqueda'
            }
    
    @staticmethod
    @transaction.atomic
    def crear_venta(items_data, usa_voz=True, dispositivo='Web'):
        """
        Crear venta desde el punto de venta
        """
        try:
            if not items_data:
                raise ValueError("No hay productos en la venta")
            
            # Crear venta base
            venta = Venta.objects.create(
                cliente_nombre='Cliente POS',
                total=0
            )
            
            total = 0
            items_creados = []
            
            # Crear items
            for item_data in items_data:
                producto = Producto.objects.get(id=item_data['producto_id'])
                cantidad = item_data['cantidad']
                
                # Validar stock
                if producto.stock < cantidad:
                    raise ValueError(f"Stock insuficiente para {producto.nombre}")
                
                # Calcular subtotal
                subtotal = producto.precio_venta * cantidad
                total += subtotal
                
                # Crear item de venta
                ItemVenta.objects.create(
                    venta=venta,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=producto.precio_venta,
                    subtotal=subtotal
                )
                
                # Actualizar stock
                producto.stock -= cantidad
                producto.save()
                
                items_creados.append({
                    'producto': producto.nombre,
                    'cantidad': cantidad,
                    'precio': float(producto.precio_venta),
                    'subtotal': float(subtotal)
                })
            
            # Actualizar total
            venta.total = total
            venta.save()
            
            # Notificar Firebase
            try:
                FirebaseService.ping_update('demo_company')
            except Exception as e:
                logger.warning(f"No se pudo notificar a Firebase: {e}")
            
            logger.info(f"Venta #{venta.id} creada: ${total}")
            
            return {
                'success': True,
                'venta_id': venta.id,
                'total': float(total),
                'items': items_creados,
                'mensaje': f'Venta registrada exitosamente: ${total:.2f}'
            }
            
        except ValueError as e:
            logger.error(f"Error de validación: {e}")
            return {
                'success': False,
                'mensaje': str(e)
            }
        except Exception as e:
            logger.error(f"Error creando venta: {e}")
            return {
                'success': False,
                'mensaje': 'Error al procesar la venta'
            }