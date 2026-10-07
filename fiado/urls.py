from django.urls import path

from . import views

app_name = 'fiado'

urlpatterns = [
    path('', views.home, name='home'),
    path('configurar-senha/', views.configurar_senha, name='configurar_senha'),
    path('cliente/<int:cliente_id>/imprimir/', views.imprimir_cliente, name='imprimir_cliente'),
    path('cliente/<int:cliente_id>/recebimento/<int:recebimento_id>/imprimir/', views.imprimir_recebimento, name='imprimir_recebimento'),
    path('cliente/<int:cliente_id>/receber/', views.receber_cliente, name='receber_cliente'),
    path('cliente/<int:cliente_id>/', views.cliente_historico, name='cliente_historico'),
    path('<int:id>/', views.detalhe, name='detalhe'),
    path('<int:id>/pago/', views.marcar_pago, name='marcar_pago'),
]
