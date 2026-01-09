from django.contrib.auth import logout
from django.utils.timezone import now
from datetime import timedelta
from django.shortcuts import redirect 
from django.conf import settings
from datetime import datetime

class SessionTimeOut:
    def __init__(self, get_response):
        self.get_response = get_response 
    
    def __call__(self, request): 
        if request.user.is_authenticated:
            last_login_str = request.session.get("last_login")
            
            if last_login_str:
                last_login = datetime.fromisoformat(last_login_str)
                
                if now() - last_login > timedelta(seconds=settings.SESSION_COOKIE_AGE):
                    # Sesión cadudada 
                    logout(request)
                    return redirect("custom_auth:session_expired")
        
        response = self.get_response(request)
        return response