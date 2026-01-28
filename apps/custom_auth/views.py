from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.urls import reverse
from django.core.mail import EmailMessage
from django.core import signing
from django.contrib.auth.hashers import make_password
from django.utils.dateparse import parse_date
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from PredictaAI.tokens import account_activation_token
from django.contrib.auth import get_user_model

from .forms.login import LoginForm
from .forms.signup import SignUpForm

def login_view(request): 
    if request.user.is_authenticated:
        return redirect("companies:dashboard")
    
    if request.method == "POST": 
        form = LoginForm(request.POST) 
        
        if form.is_valid(): 
            login(request, form.get_user())
            request.session["last_login"] = now().isoformat()
            
            return redirect("companies:dashboard")
                     
    else:
        form = LoginForm()
        
    return render(
        request, 
        "custom_auth/login.html", 
        {"form": form}
    )

def signup_view(request): 
    if request.user.is_authenticated: 
        return redirect("companies:dashboard")
    
    if request.method == "POST":
        form = SignUpForm(request.POST)
        
        if form.is_valid(): 
            # Do NOT persist the user yet. Create a signed payload with the cleaned data
            current_site = get_current_site(request)
            mail_subject = "Activación de la cuenta"

            payload = {
                "first_name": form.cleaned_data.get("first_name"),
                "last_name": form.cleaned_data.get("last_name"),
                "username": form.cleaned_data.get("username"),
                "email": form.cleaned_data.get("email"),
                "password": make_password(form.cleaned_data.get("password1")),
                "birth_date": form.cleaned_data.get("birth_date").isoformat() if form.cleaned_data.get("birth_date") else None,
            }

            signed = signing.dumps(payload, salt="signup")
            activation_path = reverse("custom_auth:activate_signed", kwargs={"signed": signed})
            activation_link = f"{request.scheme}://{current_site.domain}{activation_path}"

            message = render_to_string(
                "custom_auth/activation_email.html",
                {
                    "user": type("U", (), {"first_name": payload.get("first_name"), "username": payload.get("username")}),
                    "domain": current_site.domain,
                    "activation_link": activation_link,
                }
            )

            to_email = form.cleaned_data.get("email")
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.content_subtype = "html"
            email.send()

            # render same template and show modal instructing user to check email
            new_form = SignUpForm()
            return render(
                request,
                "custom_auth/signup.html",
                {"form": new_form, "show_verification_modal": True, "email": to_email},
            )
    else: 
        form = SignUpForm()
    
    return render(
        request, 
        "custom_auth/signup.html",
        {"form": form}
    )

@login_required
def signup_done_view(request):
    return render(request, "custom_auth/signup_done.html")
    
@login_required 
def logout_view(request): 
    logout(request)
    return redirect("core:home")

def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()

        login(request, user)
        return redirect("custom_auth:signup_done")
    else:
        messages.error(request, "El enlace expiró o es inválido")
        return redirect("custom_auth:signup")

def activate_signed(request, signed):
    # Consume a signed payload and create the user only when this link is visited.
    User = get_user_model()
    try:
        payload = signing.loads(signed, salt="signup", max_age=60 * 60 * 24)  # 1 day
    except signing.SignatureExpired:
        messages.error(request, "El enlace de activación expiró.")
        return redirect("custom_auth:signup")
    except signing.BadSignature:
        messages.error(request, "El enlace de activación no es válido.")
        return redirect("custom_auth:signup")

    # Check duplicates
    if User.objects.filter(username=payload.get("username")).exists():
        messages.error(request, "El nombre de usuario ya está registrado.")
        return redirect("custom_auth:signup")

    if User.objects.filter(email=payload.get("email")).exists():
        messages.error(request, "El correo electrónico ya está registrado.")
        return redirect("custom_auth:signup")

    # create user
    birth_date = None
    if payload.get("birth_date"):
        try:
            birth_date = parse_date(payload.get("birth_date"))
        except Exception:
            birth_date = None

    user = User(
        username=payload.get("username"),
        email=payload.get("email"),
        first_name=payload.get("first_name") or "",
        last_name=payload.get("last_name") or "",
    )

    if hasattr(user, "birth_date") and birth_date:
        setattr(user, "birth_date", birth_date)

    # payload stores hashed password
    user.password = payload.get("password")
    user.is_active = True
    user.save()

    login(request, user)
    return redirect("custom_auth:signup_done")

@login_required
def session_expired(request):
    return render(request, "custom_auth/session_expired.html")
