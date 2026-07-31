from django.urls import path
from vendas import views

app_name = 'vendas'

urlpatterns = [
    path('', views.home, name='home'),
    path('inicial/', views.Pinicial, name='Pinicial'),
]