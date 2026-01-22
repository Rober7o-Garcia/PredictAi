from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
import logging

from .services.venta_service import VentaService
from .services.chatbot_voz_service import ChatbotVozService

logger = logging.getLogger(__name__)

def punto_venta(request):
    """Vista principal del punto de venta"""
    return render(request, 'punto_venta.html')

@require_http_methods(["GET"])
def buscar_producto_por_codigo(request, codigo):
    """API: Buscar producto por código de barras"""
    resultado = VentaService.buscar_producto_por_codigo(codigo)
    
    if resultado['encontrado']:
        return JsonResponse(resultado)
    else:
        status = 404 if not resultado.get('multiples') else 200
        return JsonResponse(resultado, status=status)

@require_http_methods(["POST"])
def crear_venta(request):
    """API: Crear venta"""
    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        usa_voz = data.get('usa_voz', True)
        dispositivo = data.get('dispositivo', 'Web')
        
        resultado = VentaService.crear_venta(
            items_data=items,
            usa_voz=usa_voz,
            dispositivo=dispositivo
        )
        
        if resultado['success']:
            return JsonResponse(resultado)
        else:
            return JsonResponse(resultado, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'mensaje': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f"Error en crear_venta: {e}")
        return JsonResponse({'success': False, 'mensaje': 'Error del servidor'}, status=500)

@require_http_methods(["POST"])
def interpretar_comando_voz(request):
    """API: Interpretar comando de voz"""
    try:
        data = json.loads(request.body)
        texto = data.get('texto', '')
        contexto = data.get('contexto', {})
        
        if not texto:
            return JsonResponse({
                'accion': 'pedir_aclaracion',
                'respuesta_chatbot': 'No escuché nada.'
            })
        
        resultado = ChatbotVozService.interpretar_comando_voz(texto, contexto)
        return JsonResponse(resultado)
        
    except Exception as e:
        logger.error(f"Error en comando voz: {e}")
        return JsonResponse({
            'accion': 'pedir_aclaracion',
            'respuesta_chatbot': 'Error procesando comando'
        }, status=500)