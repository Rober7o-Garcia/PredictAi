"""
API Views
Endpoints REST para operaciones desde móvil/apps externas
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
import logging

from .services import SalesService

logger = logging.getLogger(__name__)


@api_view(['POST'])
@csrf_exempt
def create_venta_api(request):
    """
    API endpoint para crear ventas desde móvil u otras apps
    
    POST /companies/api/ventas/
    """
    try:
        items_data = request.data.get('items', [])
        cliente_nombre = request.data.get('cliente_nombre')
        notas = request.data.get('notas')
        
        if not items_data:
            return Response(
                {'error': 'Debe incluir al menos un producto en "items"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not isinstance(items_data, list):
            return Response(
                {'error': '"items" debe ser una lista'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        for item in items_data:
            if 'producto_id' not in item:
                return Response(
                    {'error': 'Cada item debe tener "producto_id"'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if 'cantidad' not in item:
                return Response(
                    {'error': 'Cada item debe tener "cantidad"'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if item['cantidad'] <= 0:
                return Response(
                    {'error': 'La cantidad debe ser mayor a 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        venta = SalesService.crear_venta(
            items_data=items_data,
            cliente_nombre=cliente_nombre,
            notas=notas
        )
        
        logger.info(f"📱 Venta creada via API: #{venta.id} - ${venta.total}")
        
        return Response({
            'success': True,
            'venta_id': venta.id,
            'total': float(venta.total),
            'items_count': venta.items.count(),
            'message': '✅ Venta registrada. Dashboard actualizado automáticamente.'
        }, status=status.HTTP_201_CREATED)
        
    except ValueError as e:
        logger.warning(f"Error de validación en API: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error interno en API: {e}")
        return Response(
            {'error': 'Error interno del servidor', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def test_firebase(request):
    """
    Endpoint de testing para verificar conexión con Firebase
    
    GET /companies/api/test-firebase/
    """
    from .services import FirebaseService
    
    success = FirebaseService.test_connection()
    
    if success:
        return Response({
            'status': 'ok',
            'message': '✅ Conexión a Firebase exitosa'
        })
    else:
        return Response({
            'status': 'error',
            'message': '❌ No se pudo conectar a Firebase'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
def dashboard_data(request):
    """
    API endpoint para obtener datos del dashboard
    
    GET /companies/api/dashboard-data/
    
    Response:
    {
        "liquidez": 1940.05,
        "margen_neto_porcentaje": 49.66,
        "ticket_promedio": 47.32,
        "ventas_mes": 1940.05,
        "labels_meses": [...],
        "datos_meses": [...],
        "labels_productos": [...],
        "datos_productos": [...],
        "labels_categorias": [...],
        "datos_categorias": [...],
        "labels_flujo": [...],
        "datos_ingresos": [...],
        "datos_egresos": [...],
        "productos_reponer": [...],
        "productos_reponer_count": 0
    }
    """
    try:
        from .services import DashboardService
        
        # Obtener todos los datos del dashboard
        data = DashboardService.get_dashboard_data()
        
        logger.info("📊 Dashboard data solicitado via API")
        
        return Response(data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error al obtener datos del dashboard: {e}")
        return Response(
            {'error': 'Error al obtener datos del dashboard', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )