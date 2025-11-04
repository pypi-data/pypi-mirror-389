from django.db import models
from django.utils.translation import gettext_lazy as _

class ItemRegistrado(models.Model):
    nome = models.CharField(max_length=100, verbose_name=_("Nome do Item"))
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Item Registrado")
        verbose_name_plural = _("Itens Registrados")
        ordering = ['criado_em']

    def __str__(self):
        return self.nome

def soma_um_e_dois():
    print("Calculando a soma de 1 + 2...")
    return 1 + 2
