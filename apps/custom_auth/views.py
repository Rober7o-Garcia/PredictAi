from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
  
from .forms.login import LoginForm
from .forms.signup import SignUpForm

def login_view(request): 
    if request.user.is_authenticated:
        return redirect("gameplay:start-game")
    
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

def signup_done_view(request):
    if request.user.is_authenticated: 
        return redirect("gameplay:start-game")
    
    return render(request, "custom_auth/signup_done.html")

def signup_view(request): 
    if request.user.is_authenticated: 
        return redirect("gameplay:start-game")
    
    if request.method == "POST":
        form = SignUpForm(request.POST)
        
        if form.is_valid(): 
            form.save()
            return redirect("custom_auth:signup_done")
    else: 
        form = SignUpForm()
    
    return render(
        request, 
        "custom_auth/signup.html",
        {"form": form}
    )
    
@login_required 
def logout_view(request): 
    logout(request)
    return redirect("core:home")

@login_required
def session_expired(request):
    return render(request, "custom_auth/session_expired.html")
