from django.urls import path
from . import views

urlpatterns = [
    path('', views.sermon_list, name='sermon_list'),
    path('sermon/<uuid:pk>/', views.sermon_detail, name='sermon_detail'),
    path('sermon/<uuid:pk>/question/', views.submit_question, name='submit_question'),
    path('webhook/whatsapp/', views.whatsapp_webhook, name='whatsapp_webhook'),
]
