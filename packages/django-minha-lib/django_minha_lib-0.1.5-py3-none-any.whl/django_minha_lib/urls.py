from django.urls import path
from .views import PaginaInicialView

app_name = 'minha_lib'  # Nome do namespace da lib

urlpatterns = [
    # A URL será acessada como: /lib-path/
    path('', PaginaInicialView.as_view(), name='pagina_inicial'),
]
