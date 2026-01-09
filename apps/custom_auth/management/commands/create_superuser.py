from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.custom_auth.validators.email import validar_email
from apps.custom_auth.validators.name import validar_nombre
from apps.custom_auth.validators.username import validar_username
from apps.custom_auth.validators.password import validar_password

from colorama import Fore 
from getpass import getpass

User = get_user_model()

def verificar_email(email):
    if User.objects.filter(email=email).exists():
        raise ValidationError(Fore.RED + f"El email '{email}' ya se encuentra registrado" + Fore.RESET)

def verificar_username(username):
    if User.objects.filter(username=username).exists():
        raise ValidationError(Fore.RED + f"El username '{username}' ya se encuentra registrado" + Fore.RESET)

class Command(BaseCommand):
    def __init__(self):
        super().__init__()
        self.campos = ["first_name", "last_name", "username", "email", "password"]
        self.data = {}
        self.info = {
            "first_name": [
                validar_nombre  
            ],
            
            "last_name": [
                validar_nombre    
            ],
            
            "username": [
                validar_username, 
                verificar_username
            ],
            
            "email": [
                validar_email,
                verificar_email 
            ],
            
            "password": [
                validar_password
            ],
        }
        
    
    def get_input(self, field_name): 
        field = Fore.LIGHTCYAN_EX +  f"Ingrese su {field_name}: " + Fore.RESET
        return getpass(field) if field_name in ["password", "confirm_password"] else input(field)
    
    def handle(self, *args, **options):
        try:
            for campo in self.campos:
                while True: 
                    try:
                        entrada = self.get_input(campo).strip()
                        validaciones = self.info[campo]
                        
                        for validacion in validaciones:
                            validacion(entrada)
                            
                    except ValidationError as err1:
                        print(Fore.RED + f"{err1}\n\n" + Fore.RESET)
                    
                    else:
                        self.data[campo] = entrada 
                        break
        
            while True:
                try:
                    entrada_f = self.get_input("confirm_password").strip()
                    validar_password(entrada_f)
                    if self.data["password"] != entrada_f:
                        raise ValidationError("Las contraseñas no coinciden")
                except ValidationError as err:
                    print(Fore.RED + f"{err}\n" + Fore.RESET)
                else:
                    break
                
            User.objects.create_superuser(**self.data)
            self.stdout.write(Fore.LIGHTGREEN_EX + "Super usuario creado correctamente!" + Fore.RESET)
        except KeyboardInterrupt:
            print(Fore.YELLOW + "\n\n ⚠️  Ejecución del programa interrumpida ⚠️\n" + Fore.RESET)
    
    

