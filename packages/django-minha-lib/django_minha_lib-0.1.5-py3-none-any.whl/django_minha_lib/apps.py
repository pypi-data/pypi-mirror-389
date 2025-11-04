from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class MinhaLibConfig(AppConfig):
    # O nome curto para a configuração (deve ser o nome do diretório)
    name = 'django_minha_lib'

    # O nome que aparece no painel de administração (admin)
    verbose_name = _('Minha Biblioteca Reutilizável')

    def ready(self):
        # Aqui você pode colocar lógica que deve ser executada quando o Django carrega o app.
        pass
