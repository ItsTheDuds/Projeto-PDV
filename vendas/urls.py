from django.urls import path

from . import views

app_name = 'vendas'

urlpatterns = [
    path('', views.home, name='home'),
    path('historico/', views.historico, name='historico'),
    path('resumo-periodo/', views.resumo_periodo, name='resumo_periodo'),
    path('comprovante/<int:id>/', views.comprovante, name='comprovante'),
    path('<int:id>/', views.detalhe, name='detalhe'),
    path('finalizar/', views.finalizar, name='finalizar'),
]
