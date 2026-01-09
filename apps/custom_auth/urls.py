from django.urls import path
from .views import login_view, signup_done_view, signup_view, logout_view, session_expired

app_name = 'custom_auth'

urlpatterns = [
    path(
        "login/", login_view, name="login"
    ),
    
    path(
        "signup-done/", signup_done_view, name="signup_done"
    ),
    
    path(
        "signup/", signup_view, name="signup"
    ),
    
    path(
        "logout/", 
        logout_view, 
        name="logout"
    ),

    path("session_expired/", session_expired, name="session_expired")  
]