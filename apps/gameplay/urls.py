from django.urls import path
from . import views

app_name = 'gameplay'

urlpatterns = [
    path('chat/', views.chatbot, name='chatbot'),
    path('chat/<int:conversacion_id>/', views.chatbot, name='chatbot_conversacion'),
    path('chat/api/', views.chatbot_api, name='chatbot_api'),
    path('chat/nueva/', views.nueva_conversacion, name='nueva_conversacion'),
    path('chat/eliminar/<int:conversacion_id>/', views.eliminar_conversacion, name='eliminar_conversacion'),
    path('chat/mensajes/<int:conversacion_id>/', views.obtener_mensajes_conversacion, name='obtener_mensajes'), 
    path('insights/<int:insight_id>/descartar/', views.descartar_insight, name='descartar_insight'),
    path('insights/descartar-todos/', views.descartar_todos_insights, name='descartar_todos_insights'),

]
