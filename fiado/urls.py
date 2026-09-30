from django.urls import path

from . import views

app_name = 'fiado'

urlpatterns = [
    path('', views.home, name='home'),
    path('configurar-senha/', views.configurar_senha, name='configurar_senha'),
    path('<int:id>/', views.detalhe, name='detalhe'),
    path('<int:id>/pago/', views.marcar_pago, name='marcar_pago'),
    path('cliente/<int:cliente_id>/', views.cliente_historico, name='cliente_historico'),
]
