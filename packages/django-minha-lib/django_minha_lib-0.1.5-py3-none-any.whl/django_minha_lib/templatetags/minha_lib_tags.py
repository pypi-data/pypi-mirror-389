import time

from django import template

# Crie uma instância da biblioteca de templates
register = template.Library()


# Use o decorador simple_tag para registrar a função como uma template tag
@register.simple_tag
def show_today_timestamp():
    """
    Retorna o timestamp Unix atual (segundos desde a época).
    """
    # time.time() retorna o timestamp como um float
    timestamp = int(time.time())

    # mark_safe é opcional aqui, mas é uma boa prática se a saída fosse HTML puro
    return str(timestamp)


# --- Exemplo de como você faria se a tag precisasse de argumentos ---
@register.simple_tag
def saudacao(nome):
    """Retorna uma saudação personalizada."""
    return f"Olá, {nome}!"
