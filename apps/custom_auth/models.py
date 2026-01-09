from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from apps.custom_auth.validators.email import validar_email
from apps.custom_auth.validators.name import validar_nombre
from apps.custom_auth.validators.username import validar_username
from apps.custom_auth.validators.password import validar_password
from django.contrib.auth.password_validation import validate_password

class CustomUserManager(BaseUserManager): 
    def create_user(self, email, password=None, **extra_fields): 
        if not email: 
            raise ValueError("El correo es obligatorio")
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        
        if password:
            validar_password(password)                  # Regex
            validate_password(password, user=user)      # Django nativo

        
        user.set_password(password)
        user.save(using=self._db)
        return user
        
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")

        return self.create_user(email, password, **extra_fields)

    
class CustomUser(AbstractBaseUser, PermissionsMixin): 
    first_name = models.CharField(max_length=30, validators=[validar_nombre])
    last_name = models.CharField(max_length=30, validators=[validar_nombre])
    username = models.CharField(max_length=20, validators=[validar_username], unique=True)
    email = models.EmailField(max_length=254, validators=[validar_email], unique=True)
    password = models.CharField(max_length=128)      # Lo guarda 
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "username"]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self): 
        return f"{self.first_name} {self.last_name}"
    
    def get_short_name(self): 
        return self.first_name
    
    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

