from django.urls import path
from . import views

app_name = 'gameplay'

urlpatterns = [
    path('chat/', views.chatbot, name='chatbot'),
]