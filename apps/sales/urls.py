from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.punto_venta, name='punto_venta'),
    path('api/producto/<str:codigo>/', views.buscar_producto_por_codigo, name='buscar_producto'),
    path('api/venta/', views.crear_venta, name='crear_venta'),
    path('api/comando-voz/', views.interpretar_comando_voz, name='comando_voz'),
]