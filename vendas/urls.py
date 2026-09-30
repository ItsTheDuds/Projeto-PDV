from django.urls import path

from . import views

app_name = 'vendas'

urlpatterns = [
    path('', views.home, name='home'),
    path('finalizar/', views.finalizar, name='finalizar'),
]
