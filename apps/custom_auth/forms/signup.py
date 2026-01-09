from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from apps.custom_auth.validators.password import validar_password
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class SignUpForm(UserCreationForm):    
    password1 = forms.CharField(
        max_length=128,
        required=True,
        validators=[validar_password],
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "password",
                "minlength": "8",
                "maxlength": "128",
                "class": "bg-gray-200 px-3 py-2 outline-0 w-72 max-md:w-[70vw]"
            }
        )
    )
        
    password2 = forms.CharField(
        max_length=128,
        required=True,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "confirm password",
                "minlength": "8",
                "maxlength": "128",
                "class": "bg-gray-200 px-3 py-2 outline-0 w-72 max-md:w-[70vw]"
            }
        )
    )
    
    first_name = forms.CharField(
        required=True, 
        widget=forms.TextInput(
            attrs={
                "placeholder": "first_name",
                "minlength": "3",
                "maxlength": "30",
                "class": "bg-gray-200 px-3 py-2 outline-0 w-72 max-md:w-[70vw]"
            }
        )
    )
    
    last_name = forms.CharField(
        required=True, 
        widget=forms.TextInput(
            attrs={
                "placeholder": "last_name",
                "minlength": "3",
                "maxlength": "30",
                "class": "bg-gray-200 px-3 py-2 outline-0 w-72 max-md:w-[70vw]"
            }
        )
    )
    
    username = forms.CharField(
        required=True, 
        widget=forms.TextInput(
            attrs={
                "placeholder": "username",
                "minlength": "6",
                "maxlength": "20",
                "class": "bg-gray-200 px-3 py-2 outline-0 w-72 max-md:w-[70vw]"
            }
        )
    )
    
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(
            attrs={
                "placeholder": "email",
                "minlength": "6",
                "maxlength": "254",
                "class": "bg-gray-200 px-3 py-2 outline-0 w-72 max-md:w-[70vw]"
            }
        )
    )
    
    class Meta: 
        model = User
        fields = ["first_name", "last_name", "username", "email"]
        
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
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False   # 🔴 clave
        if commit:
            user.save()
        return user
