from django.core.validators import RegexValidator

validar_nombre = RegexValidator(
    regex=r"^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]{3,30}$",
    message="El formato del nombre / apellido tiene un formato inválido. No debe tener números ni caracteres especiales (incluyendo el signo _)), su longitud debe estar entre los 3 y 30 caracteres"
) 