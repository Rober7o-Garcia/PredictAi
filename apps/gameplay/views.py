from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
import json

from .services.openai_service import interpretar_mensaje
from .services.negocio_service import ejecutar_accion
from apps.gameplay.models import MensajeChat, Conversacion


def chatbot(request, conversacion_id=None):
    """Vista principal del chatbot"""
    
    if conversacion_id:
        # Si viene con ID, usar esa conversación
        conversacion_actual = get_object_or_404(Conversacion, id=conversacion_id)
    else:
        # ✅ Si no hay ID, buscar la conversación más reciente
        conversacion_actual = Conversacion.objects.first()
        
        # Si no hay ninguna conversación, crear una
        if not conversacion_actual:
            conversacion_actual = Conversacion.objects.create()
        
        # Redirigir a la URL con el ID para evitar crear duplicados al recargar
        return redirect('gameplay:chatbot_conversacion', conversacion_id=conversacion_actual.id)
    
    # Cargar mensajes de la conversación actual
    mensajes = conversacion_actual.mensajes.all()
    
    # Listar todas las conversaciones para el sidebar
    conversaciones = Conversacion.objects.all()[:20]
    
    return render(request, 'chatbot.html', {
        'conversacion_actual': conversacion_actual,
        'mensajes': mensajes,
        'conversaciones': conversaciones
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

    # Obtener conversación
    conversacion = get_object_or_404(Conversacion, id=conversacion_id)

    # ✅ GUARDAR MENSAJE DEL USUARIO
    MensajeChat.objects.create(
        conversacion=conversacion,
        tipo='user',
        mensaje=mensaje
    )
    
    # Verificar si es el primer mensaje
    es_primer_mensaje = conversacion.mensajes.count() == 1
    
    # Generar título automático si es el primer mensaje
    if es_primer_mensaje:
        conversacion.generar_titulo_automatico()

    # Interpretar con OpenAI
    data = interpretar_mensaje(mensaje)

    if not data:
        respuesta = "⚠️ No entendí tu mensaje, intenta decirlo de otra forma."
    else:
        respuesta = ejecutar_accion(data)

    # ✅ GUARDAR RESPUESTA DEL BOT
    MensajeChat.objects.create(
        conversacion=conversacion,
        tipo='bot',
        mensaje=respuesta
    )
    
    # Actualizar fecha de actualización
    conversacion.save()

    # ✅ DEVOLVER TAMBIÉN EL TÍTULO SI ES EL PRIMER MENSAJE
    response_data = {"respuesta": respuesta}
    
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
        "url": f"/gameplay/chat/{conversacion.id}/"
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
            "redirect_url": f"/gameplay/chat/{conversacion_restante.id}/"
        })
    else:
        # Si no quedan conversaciones, crear una nueva
        nueva_conv = Conversacion.objects.create()
        return JsonResponse({
            "success": True,
            "redirect_url": f"/gameplay/chat/{nueva_conv.id}/"
        })