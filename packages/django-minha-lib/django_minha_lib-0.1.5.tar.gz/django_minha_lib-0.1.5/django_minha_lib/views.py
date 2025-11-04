from django.shortcuts import render
from django.views import View


class PaginaInicialView(View):
    def get(self, request):
        context = {
            'url_pypi': 'https://pypi.org/project/django-minha-lib/',
        }
        # O Django procurará por 'django_minha_lib/pagina_inicial.html'
        return render(request, 'django_minha_lib/pagina_inicial.html', context)
