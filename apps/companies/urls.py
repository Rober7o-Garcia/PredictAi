from django.urls import path
from . import views

app_name = 'companies' 

urlpatterns = [
    path('', views.dashboard, name='dashboard'),  # <-- Cadena vacía aquí
    path('api/dashboard-data/', views.dashboard_data, name='dashboard_data'),  # Nueva ruta

]