from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
import logging
from .services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def dashboard(request):
    """
    Vista principal del dashboard.
    Renderiza el template con las métricas iniciales.
    """
    try:
        data = DashboardService.get_dashboard_data()
        
        context = {
            # Nuevos KPIs
            'liquidez': data.get('liquidez', 0),
            'margen_neto_porcentaje': data.get('margen_neto_porcentaje', 0),
            'ticket_promedio': data.get('ticket_promedio', 0),
            'ventas_mes': data.get('ventas_mes', 0),
            
            # Datos viejos (compatibilidad)
            'ventas_hoy': data.get('ventas_hoy', 0),
            'ganancia_mes': data.get('ganancia_mes', 0),
            'productos_top': data.get('productos_top', []),
            'productos_margen': data.get('productos_margen', []),
            'productos_reponer': data.get('productos_reponer', []),
            'labels_semana': json.dumps(data.get('labels_semana', [])),
            'datos_semana': json.dumps(data.get('datos_semana', [])),
        }
        
        return render(request, 'dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error al cargar dashboard: {e}")
        context = {
            'liquidez': 0,
            'margen_neto_porcentaje': 0,
            'ticket_promedio': 0,
            'ventas_mes': 0,
            'ventas_hoy': 0,
            'ganancia_mes': 0,
            'productos_top': [],
            'productos_margen': [],
            'productos_reponer': [],
            'labels_semana': json.dumps([]),
            'datos_semana': json.dumps([]),
            'error': 'Error al cargar los datos del dashboard'
        }
        return render(request, 'dashboard.html', context)
    


@require_http_methods(["GET"])
def dashboard_data(request):
    """
    API endpoint que devuelve los datos del dashboard en JSON.
    Usado para las actualizaciones automáticas.
    """
    try:
        # Obtener todos los datos usando el servicio
        # (Ya vienen serializados desde dashboard_service.py)
        data = DashboardService.get_dashboard_data()
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Error al obtener datos del dashboard: {e}")
        return JsonResponse(
            {
                'error': 'Error al obtener los datos',
                'message': str(e)
            },
            status=500
        )