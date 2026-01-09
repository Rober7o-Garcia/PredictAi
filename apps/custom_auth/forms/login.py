from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model, authenticate

from apps.custom_auth.validators.email import validar_email

User = get_user_model()

class LoginForm(forms.Form): 
    email = forms.EmailField(
        validators=[validar_email],
        max_length=254,
        required=True,
        widget=forms.EmailInput(
            attrs={
                "placeholder": "email",
                "minlength": "6",
                "maxlength": "254", 
                "class": "bg-gray-200 px-3 py-2 outline-0 w-80 max-md:w-[60vw]"
            }
        )
    )
    
    password = forms.CharField(
        required=True,
        max_length=128,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "password",
                "minlength": "8",
                "maxlength": "128",
                "class": "bg-gray-200 px-3 py-2 outline-0 w-80 max-md:w-[60vw]"
            }
        )
    )
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        
        if email and password:
            user = authenticate(email=email, password=password)
        
            if user is None: 
                raise ValidationError("Este correo no está registrado o las credenciales no coinciden.")
            
            if not user.is_active:
                raise ValidationError("El usuario está inactivo")
            
            # guarda el usuario autenticado en la instancia del formulario   
            self.user = user    
        
        return cleaned_data
    
    def clean_email(self):
        email = self.cleaned_data.get("email", "")
        email =  email.lower().strip()

        return email
    
    def clean_password(self): 
        password = self.cleaned_data.get("password", "")
        password = password.strip()
        
        return password
    
    def get_user(self): 
        return getattr(self, "user", None)