from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
import json
from .services.openai_service import interpretar_mensaje
from .services.negocio_service import ejecutar_accion
from apps.chatbot.models import MensajeChat, Conversacion
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .services.intelligent_business_assistant import asistente_negocio
from .services.openai_service import interpretar_mensaje
from .services.negocio_service import ejecutar_accion
from .services.memory_manager import procesar_y_guardar_conocimiento
from .services.pattern_analyzer import ejecutar_analisis_completo, obtener_insights_no_vistos
from .models import MensajeChat, Conversacion, InsightNegocio  # ✅ Agregar InsightNegocio
from django.utils import timezone
from .services.text_formatter import formatear_respuesta_chatbot

def chatbot(request, conversacion_id=None):
    """Vista principal del chatbot"""
    
    if conversacion_id:
        conversacion_actual = get_object_or_404(Conversacion, id=conversacion_id)
    else:
        conversacion_actual = Conversacion.objects.first()
        
        if not conversacion_actual:
            conversacion_actual = Conversacion.objects.create()
        
        return redirect('chatbot:chatbot_conversacion', conversacion_id=conversacion_actual.id)
    
    # ✅ EJECUTAR ANÁLISIS DE PATRONES (si hace más de 24 horas del último)
    from .models import InsightNegocio
    ultimo_insight = InsightNegocio.objects.first()
    
    if not ultimo_insight or (timezone.now() - ultimo_insight.detectado_en).days >= 1:
        # Ejecutar en background (o síncronamente para demo)
        ejecutar_analisis_completo()
    
    # Cargar mensajes de la conversación actual
    mensajes = conversacion_actual.mensajes.all()
    
    # Listar todas las conversaciones para el sidebar
    conversaciones = Conversacion.objects.all()[:20]
    
    # ✅ OBTENER INSIGHTS NO VISTOS
    insights_pendientes = obtener_insights_no_vistos()[:5]  # Máximo 5
    
    return render(request, 'chatbot/chatbot.html', {
        'conversacion_actual': conversacion_actual,
        'mensajes': mensajes,
        'conversaciones': conversaciones,
        'insights_pendientes': insights_pendientes,  # ✅ NUEVO
    })


@require_POST
def chatbot_api(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"respuesta": "❌ Formato de mensaje inválido"},
            status=400
        )

    mensaje = body.get("mensaje")
    conversacion_id = body.get("conversacion_id")
    
    if not mensaje:
        return JsonResponse({"respuesta": "❌ Mensaje vacío"})
    
    if not conversacion_id:
        return JsonResponse({"error": "❌ ID de conversación requerido"}, status=400)

    conversacion = get_object_or_404(Conversacion, id=conversacion_id)

    # Guardar mensaje del usuario
    MensajeChat.objects.create(
        conversacion=conversacion,
        tipo='user',
        mensaje=mensaje
    )
    
    es_primer_mensaje = conversacion.mensajes.count() == 1
    
    if es_primer_mensaje:
        conversacion.generar_titulo_automatico()

    # OBTENER HISTORIAL DE LA CONVERSACIÓN (últimos 10 mensajes)
    mensajes_previos = conversacion.mensajes.order_by('-fecha')[:10]
    historial = []
    
    for msg in reversed(mensajes_previos):
        historial.append({
            "role": "user" if msg.tipo == "user" else "assistant",
            "content": msg.mensaje
        })

    # Palabras clave de ESCRITURA (modificar datos)
    keywords_escritura = [
        'registrar', 'registra', 'vendí', 'vender', 'vende',
        'agregar', 'agrega', 'crear', 'crea', 'añadir', 'añade'
    ]
    
    es_accion_escritura = any(word in mensaje.lower() for word in keywords_escritura)
    
    if es_accion_escritura:
        # Sistema antiguo para registros
        data = interpretar_mensaje(mensaje)
        respuesta = ejecutar_accion(data)
    else:
        # Sistema inteligente
        respuesta = asistente_negocio(mensaje, historial=historial)
        
    
    # ✅ FORMATEAR LA RESPUESTA (convertir markdown a HTML)
    respuesta_formateada = formatear_respuesta_chatbot(respuesta)

    # ✅ EXTRAER Y GUARDAR CONOCIMIENTO DESPUÉS DE RESPONDER
    resultado_memoria = procesar_y_guardar_conocimiento(mensaje, respuesta)
    
    if resultado_memoria['conocimiento_guardado']:
        print(f"💾 Conocimiento guardado: {resultado_memoria['items']}")

    # Guardar respuesta del bot
    MensajeChat.objects.create(
        conversacion=conversacion,
        tipo='bot',
        mensaje=respuesta_formateada
    )
    
    conversacion.save()

    response_data = {"respuesta": respuesta_formateada}
    
    if es_primer_mensaje:
        response_data["nuevo_titulo"] = conversacion.titulo
        response_data["es_primer_mensaje"] = True

    return JsonResponse(response_data)


@require_POST
def nueva_conversacion(request):
    """Crear nueva conversación"""
    conversacion = Conversacion.objects.create()
    return JsonResponse({
        "conversacion_id": conversacion.id,
        "url": f"/chatbot/chat/{conversacion.id}/",
        "titulo": conversacion.titulo,  # ✅ AGREGAR
        "fecha_actualizacion": conversacion.fecha_actualizacion.strftime('%d/%m/%Y %H:%M')  # ✅ AGREGAR
    })


@require_http_methods(["DELETE"])
def eliminar_conversacion(request, conversacion_id):
    """Eliminar conversación"""
    conversacion = get_object_or_404(Conversacion, id=conversacion_id)
    conversacion.delete()
    
    # ✅ Después de eliminar, buscar otra conversación para redirigir
    conversacion_restante = Conversacion.objects.first()
    
    if conversacion_restante:
        # Si hay otras conversaciones, redirigir a la más reciente
        return JsonResponse({
            "success": True,
            "redirect_url": f"/chatbot/chat/{conversacion_restante.id}/"
        })
    else:
        # Si no quedan conversaciones, crear una nueva
        nueva_conv = Conversacion.objects.create()
        return JsonResponse({
            "success": True,
            "redirect_url": f"/chatbot/chat/{nueva_conv.id}/"
        })
        
@require_GET
def obtener_mensajes_conversacion(request, conversacion_id):
    """Obtener mensajes de una conversación via AJAX"""
    conversacion = get_object_or_404(Conversacion, id=conversacion_id)
    mensajes = conversacion.mensajes.all()
    
    mensajes_data = [
        {
            'tipo': msg.tipo,
            'mensaje': msg.mensaje,
            'fecha': msg.fecha.strftime('%H:%M')
        }
        for msg in mensajes
    ]
    
    return JsonResponse({
        'conversacion_id': conversacion.id,
        'titulo': conversacion.titulo,
        'mensajes': mensajes_data
    })
    
    
@require_POST
def descartar_insight(request, insight_id):
    """Marca un insight como visto"""
    insight = get_object_or_404(InsightNegocio, id=insight_id)
    insight.visto = True
    insight.save()
    return JsonResponse({'success': True})


@require_POST
def descartar_todos_insights(request):
    """Marca todos los insights como vistos"""
    InsightNegocio.objects.filter(visto=False).update(visto=True)
    return JsonResponse({'success': True})