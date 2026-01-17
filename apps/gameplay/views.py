from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json

from .services.openai_service import interpretar_mensaje
from .services.negocio_service import ejecutar_accion


def chatbot(request):
    return render(request, 'chatbot.html')


@login_required
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
    if not mensaje:
        return JsonResponse({"respuesta": "❌ Mensaje vacío"})

    # ⬇️ YA NO USAMOS company
    data = interpretar_mensaje(mensaje)

    if not data:
        return JsonResponse({
            "respuesta": "⚠️ No entendí tu mensaje, intenta decirlo de otra forma."
        })

    respuesta = ejecutar_accion(data)

    return JsonResponse({"respuesta": respuesta})
