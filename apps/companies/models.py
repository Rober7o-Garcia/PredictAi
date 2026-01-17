# models.py

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal

class Categoria(models.Model):
    """Categorías de productos: Libros, Cuadernos, Útiles, etc."""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Categorías"
    
    def __str__(self):
        return self.nombre


class Proveedor(models.Model):
    """Proveedores de productos"""
    nombre = models.CharField(max_length=200)
    contacto = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Proveedores"
    
    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """Productos de la librería"""
    nombre = models.CharField(max_length=200)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='productos')
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos')
    
    # Precios y costos
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    
    # Inventario
    stock_actual = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    stock_minimo = models.IntegerField(default=5, validators=[MinValueValidator(0)])
    
    # Información adicional
    codigo_barras = models.CharField(max_length=50, blank=True, null=True, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    
    # Timestamps
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} - ${self.precio_venta}"
    
    @property
    def margen_ganancia(self):
        """Calcula el margen de ganancia en porcentaje"""
        if self.precio_compra > 0:
            return ((self.precio_venta - self.precio_compra) / self.precio_compra) * 100
        return 0
    
    @property
    def ganancia_unitaria(self):
        """Ganancia por unidad vendida"""
        return self.precio_venta - self.precio_compra
    
    @property
    def necesita_reposicion(self):
        """Verifica si el stock está por debajo del mínimo"""
        return self.stock_actual <= self.stock_minimo


class Venta(models.Model):
    """Registro de ventas realizadas"""
    fecha = models.DateTimeField(default=timezone.now)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Información opcional del cliente
    cliente_nombre = models.CharField(max_length=200, blank=True, null=True)
    
    # Metadata
    notas = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha']
    
    def __str__(self):
        return f"Venta {self.id} - ${self.total} ({self.fecha.strftime('%d/%m/%Y')})"
    
    def calcular_total(self):
        """Calcula el total de la venta basado en los items"""
        total = sum(item.subtotal for item in self.items.all())
        self.total = total
        self.save()
        return total


class ItemVenta(models.Model):
    """Items individuales de cada venta"""
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='ventas')
    
    cantidad = models.IntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Guardamos el costo al momento de la venta para análisis histórico
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name_plural = "Items de venta"
    
    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre}"
    
    @property
    def ganancia_total(self):
        """Ganancia total de este item"""
        return (self.precio_unitario - self.costo_unitario) * self.cantidad
    
    def save(self, *args, **kwargs):
        # Calcula el subtotal automáticamente
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)


class Compra(models.Model):
    """Registro de compras a proveedores"""
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='compras')
    fecha = models.DateTimeField(default=timezone.now)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    notas = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha']
    
    def __str__(self):
        return f"Compra {self.id} - {self.proveedor.nombre} (${self.total})"


class ItemCompra(models.Model):
    """Items de cada compra"""
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='compras')
    
    cantidad = models.IntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre}"
    
    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        
        # Actualiza el stock del producto
        self.producto.stock_actual += self.cantidad
        self.producto.save()