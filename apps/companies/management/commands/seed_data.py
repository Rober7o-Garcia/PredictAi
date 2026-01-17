from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from decimal import Decimal
from apps.companies.models import Categoria, Proveedor, Producto, Venta, ItemVenta, Compra, ItemCompra

class Command(BaseCommand):
    help = 'Llena la base de datos con datos de ejemplo'

    def handle(self, *args, **kwargs):
        self.stdout.write('Limpiando datos anteriores...')
        ItemVenta.objects.all().delete()
        Venta.objects.all().delete()
        ItemCompra.objects.all().delete()
        Compra.objects.all().delete()
        Producto.objects.all().delete()
        Proveedor.objects.all().delete()
        Categoria.objects.all().delete()

        self.stdout.write('Creando categorías...')
        categorias = {
            'Libros': Categoria.objects.create(nombre='Libros', descripcion='Libros de diversos géneros'),
            'Cuadernos': Categoria.objects.create(nombre='Cuadernos', descripcion='Cuadernos y libretas'),
            'Útiles Escolares': Categoria.objects.create(nombre='Útiles Escolares', descripcion='Lápices, plumas, borradores'),
            'Papelería': Categoria.objects.create(nombre='Papelería', descripcion='Hojas, folders, sobres'),
            'Arte': Categoria.objects.create(nombre='Arte', descripcion='Material de arte y manualidades'),
        }

        self.stdout.write('Creando proveedores...')
        proveedores = [
            Proveedor.objects.create(nombre='Distribuidora LibroMax', telefono='0991234567', email='ventas@libromax.com'),
            Proveedor.objects.create(nombre='Papelería El Estudiante', telefono='0987654321', email='info@elestudiante.com'),
            Proveedor.objects.create(nombre='Arte y Diseño SA', telefono='0998765432', email='contacto@artediseno.com'),
        ]

        self.stdout.write('Creando productos...')
        productos_data = [
            # Libros
            ('Cien Años de Soledad', 'Libros', 8.50, 15.00, 20, 5),
            ('Don Quijote de la Mancha', 'Libros', 10.00, 18.00, 15, 3),
            ('El Principito', 'Libros', 5.00, 10.00, 30, 5),
            ('Harry Potter y la Piedra Filosofal', 'Libros', 12.00, 22.00, 12, 3),
            ('1984 - George Orwell', 'Libros', 7.00, 13.00, 18, 4),
            ('Crónica de una Muerte Anunciada', 'Libros', 6.50, 12.00, 25, 5),
            
            # Cuadernos
            ('Cuaderno Universitario 100 hojas', 'Cuadernos', 1.20, 2.50, 80, 10),
            ('Cuaderno Espiral A4', 'Cuadernos', 1.50, 3.00, 60, 10),
            ('Libreta Pequeña 50 hojas', 'Cuadernos', 0.80, 1.50, 100, 15),
            ('Cuaderno Empastado 200 hojas', 'Cuadernos', 2.50, 5.00, 40, 8),
            ('Cuaderno de Dibujo A3', 'Cuadernos', 3.00, 6.00, 25, 5),
            
            # Útiles Escolares
            ('Lápiz Grafito HB (unidad)', 'Útiles Escolares', 0.20, 0.50, 200, 30),
            ('Borrador Blanco', 'Útiles Escolares', 0.15, 0.35, 150, 25),
            ('Sacapuntas Metálico', 'Útiles Escolares', 0.30, 0.70, 100, 20),
            ('Bolígrafo Azul', 'Útiles Escolares', 0.25, 0.60, 180, 30),
            ('Bolígrafo Negro', 'Útiles Escolares', 0.25, 0.60, 180, 30),
            ('Regla 30cm', 'Útiles Escolares', 0.50, 1.20, 70, 10),
            ('Tijeras Escolares', 'Útiles Escolares', 1.00, 2.50, 50, 8),
            ('Pegamento en Barra', 'Útiles Escolares', 0.80, 1.80, 90, 15),
            ('Corrector Líquido', 'Útiles Escolares', 0.90, 2.00, 60, 10),
            
            # Papelería
            ('Resma de Papel A4 (500 hojas)', 'Papelería', 3.50, 7.00, 30, 5),
            ('Folder Manila (paquete 10)', 'Papelería', 1.00, 2.50, 40, 8),
            ('Sobres Carta (paquete 25)', 'Papelería', 1.50, 3.50, 35, 7),
            ('Papel Bond Colores (100 hojas)', 'Papelería', 2.00, 4.50, 25, 5),
            
            # Arte
            ('Caja de Colores 12 unidades', 'Arte', 2.50, 5.00, 45, 8),
            ('Caja de Colores 24 unidades', 'Arte', 4.50, 9.00, 30, 6),
            ('Temperas x6 colores', 'Arte', 3.00, 6.50, 35, 7),
            ('Pinceles Set x3', 'Arte', 2.00, 4.50, 40, 8),
            ('Cartulina A3 (unidad)', 'Arte', 0.30, 0.70, 120, 20),
            ('Marcadores Permanentes x4', 'Arte', 2.50, 5.50, 50, 10),
        ]

        productos = []
        for nombre, cat_nombre, costo, precio, stock, stock_min in productos_data:
            p = Producto.objects.create(
                nombre=nombre,
                categoria=categorias[cat_nombre],
                proveedor=random.choice(proveedores),
                precio_venta=Decimal(str(precio)),
                precio_compra=Decimal(str(costo)),
                stock_actual=stock,
                stock_minimo=stock_min,
                activo=True
            )
            productos.append(p)

        self.stdout.write('Creando ventas de los últimos 30 días...')
        hoy = timezone.now()
        
        for i in range(60):  # 60 ventas en 30 días
            # Fecha aleatoria en los últimos 30 días
            dias_atras = random.randint(0, 30)
            fecha_venta = hoy - timedelta(days=dias_atras, hours=random.randint(8, 20))
            
            # Crear venta
            venta = Venta.objects.create(fecha=fecha_venta)
            
            # Agregar entre 1 y 5 productos a la venta
            num_items = random.randint(1, 5)
            productos_vendidos = random.sample(productos, num_items)
            
            for producto in productos_vendidos:
                cantidad = random.randint(1, 5)
                
                ItemVenta.objects.create(
                    venta=venta,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=producto.precio_venta,
                    costo_unitario=producto.precio_compra,
                    subtotal=producto.precio_venta * cantidad
                )
            
            # Calcular total de la venta
            venta.calcular_total()
            
            # Actualizar stock (simular que se vendió)
            for item in venta.items.all():
                item.producto.stock_actual = max(0, item.producto.stock_actual - item.cantidad)
                item.producto.save()

        self.stdout.write(self.style.SUCCESS(f'✓ Base de datos poblada exitosamente!'))
        self.stdout.write(self.style.SUCCESS(f'  - {Categoria.objects.count()} categorías'))
        self.stdout.write(self.style.SUCCESS(f'  - {Proveedor.objects.count()} proveedores'))
        self.stdout.write(self.style.SUCCESS(f'  - {Producto.objects.count()} productos'))
        self.stdout.write(self.style.SUCCESS(f'  - {Venta.objects.count()} ventas'))
        self.stdout.write(self.style.SUCCESS(f'  - {ItemVenta.objects.count()} items vendidos'))