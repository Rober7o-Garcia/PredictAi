from django.urls import path
from . import views

app_name = 'gameplay'

urlpatterns = [
    path('chat/', views.chatbot, name='chatbot'),
    path('chatbot/api/', views.chatbot_api, name='chatbot_api'),
]
