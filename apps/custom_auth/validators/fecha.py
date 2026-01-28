from django.core.exceptions import ValidationError
from django.utils import timezone

def validar_edad(value):
    hoy = timezone.now().date()
    fecha_nacimiento = value  # ← ya es datetime.date

    edad = hoy.year - fecha_nacimiento.year - (
        (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
    )

    if edad < 16:
        raise ValidationError("Debes tener al menos 16 años.")
    if edad > 95:
        raise ValidationError("La edad no puede ser mayor a 95 años.")
