from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('clientes/', include('clientes.urls')),
    path('produtos/', include('produtos.urls')),
    path('vendas/', include('vendas.urls')),
    path('fiado/', include('fiado.urls')),
]
