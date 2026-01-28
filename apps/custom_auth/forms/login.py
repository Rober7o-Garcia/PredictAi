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
                "placeholder": "Email...",
                "minlength": "6",
                "maxlength": "254",
                "class": "w-full px-4 py-3 sm:px-8 sm:py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-blue-400 focus:bg-white"
            }
        )
    )
    
    password = forms.CharField(
        required=True,
        max_length=128,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password...",
                "minlength": "8",
                "maxlength": "128",
                "class": "w-full px-4 py-3 sm:px-8 sm:py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-blue-400 focus:bg-white"
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