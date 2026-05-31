from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('questions/', views.questions_list, name='questions_list'),
    path('api/metrics/', views.api_metrics, name='api_metrics'),
    path('questions/<uuid:pk>/retry/', views.retry_question, name='retry_question'),
]
