from django.core.validators import RegexValidator 

validar_username = RegexValidator(
    regex=r"^(?![0-9])[a-zA-Z_][a-zA-Z0-9_]{5,19}$",
    message="El formato del username es inválido. Debe tener entre 6 y 20 caracteres, no puede comenzar con un número, no puede tener caracteres especiales (excepto el _) ni espacios en blanco"
)