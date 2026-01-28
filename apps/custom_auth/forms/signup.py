from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from apps.custom_auth.validators.password import validar_password
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from apps.custom_auth.validators.fecha import validar_edad

User = get_user_model()

class SignUpForm(UserCreationForm):    
    password1 = forms.CharField(
        max_length=128,
        required=True,
        validators=[validar_password],
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password...",
                "minlength": "8",
                "maxlength": "128",
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white"
            }
        )
    )
        
    password2 = forms.CharField(
        max_length=128,
        required=True,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Confirmation password...",
                "minlength": "8",
                "maxlength": "128",
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white"
            }
        )
    )
    
    first_name = forms.CharField(
        required=True, 
        widget=forms.TextInput(
            attrs={
                "placeholder": "First name...",
                "minlength": "3",
                "maxlength": "30",
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white"
            }
        )
    )
    
    last_name = forms.CharField(
        required=True, 
        widget=forms.TextInput(
            attrs={
                "placeholder": "Last name...",
                "minlength": "3",
                "maxlength": "30",
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white"
            }
        )
    )

    birth_date = forms.DateField(
        required=True,
        validators=[validar_edad],
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white"
            }
        )
    )
    
    username = forms.CharField(
        required=True, 
        widget=forms.TextInput(
            attrs={
                "placeholder": "Username...",
                "minlength": "6",
                "maxlength": "20",
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white"
            }
        )
    )
    
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Email...",
                "minlength": "6",
                "maxlength": "254",
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white"
            }
        )
    )
    
    class Meta: 
        model = User
        fields = ["first_name", "last_name", "birth_date", "username", "email"]
        
    def clean(self): 
        cleaned_data = super().clean()

        for campo in self.Meta.fields:
            valor = cleaned_data.get(campo)
            
            if isinstance(valor, str):
                cleaned_data[campo] = valor.strip()
            
        return cleaned_data
    
    def clean_username(self): 
        username = self.cleaned_data["username"].lower().strip()
        
        if User.objects.filter(username=username).exists():
            raise ValidationError("El username ya se encuentra registrado")
    
        return username
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            validar_password(password1)   # Tu regex
            validate_password(password1)  # Validación Django
        return password1
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError("Las contraseñas no coinciden")

        return password2

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        
        if User.objects.filter(email=email).exists():
            raise ValidationError("El correo ya se encuentra registrado")
    
        return email
    
    def clean_birth_date(self):
        birth_date = self.cleaned_data["birth_date"]
        validar_edad(birth_date)

        return birth_date
