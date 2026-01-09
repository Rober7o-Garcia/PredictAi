from django.urls import path
from .views import game_view

app_name = "gameplay"

urlpatterns = [
    path("start-game/", game_view, name="start_game")    
]
