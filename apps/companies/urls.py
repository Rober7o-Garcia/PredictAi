from django.urls import path
from . import views
from . import api_views

app_name = 'companies' 

urlpatterns = [
    path('dashboard', views.dashboard, name='dashboard'),  # <-- Cadena vacía aquí
    path('api/dashboard-data/', views.dashboard_data, name='dashboard_data'),  # Nueva ruta
    path('api/ventas/', api_views.create_venta_api, name='api_create_venta'),  # ← NUEVO
    path('api/test-firebase/', api_views.test_firebase, name='api_test_firebase'),  # ← NUEVO (testing)
]