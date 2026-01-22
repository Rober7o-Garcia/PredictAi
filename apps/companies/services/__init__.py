"""
Services Package
Contiene la lógica de negocio separada de las vistas
"""

from .dashboard_service import DashboardService
from .product_service import ProductService
from .sales_service import SalesService
from .firebase_service import FirebaseService  # ← AGREGAR ESTA LÍNEA

__all__ = ['DashboardService', 'ProductService', 'SalesService', 'FirebaseService']