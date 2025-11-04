# django-minha-lib

[![PyPI](https://img.shields.io/pypi/v/django-minha-lib.svg)](https://pypi.org/project/django-minha-lib/)


> Este projeto é um teste de criação de uma biblioteca Django.

## Instalação

Você pode instalar a biblioteca usando pip ou poetry:

```bash
pip install django-minha-lib
```

ou

```bash
poetry add django-minha-lib
```

## Configuração

Adicione `django_minha_lib` à lista de `INSTALLED_APPS` no seu `settings.py`:

```python
INSTALLED_APPS = [
	# ... outras apps ...
	'django_minha_lib',
]
```

## Migrações

Após instalar e configurar, rode os comandos:

```bash
python manage.py makemigrations
python manage.py migrate
```

Pronto! Sua biblioteca Django está instalada e pronta para uso.

## Rodando localmente como desenvolvedor

Para rodar o projeto Django localmente durante o desenvolvimento, siga os passos abaixo:

```bash
git clone https://github.com/seu-usuario/django-minha-lib.git
cd django-minha-lib
poetry install
cd demo_project
pip install -e ..
poetry run ./manage.py runserver
```


## Atualizando e publicando a biblioteca

Para atualizar a versão, buildar e publicar sua biblioteca, utilize os comandos abaixo:

```bash
poetry version patch  # para avançar a versão (ex: 0.1.0 → 0.1.1)
poetry build
tar -tzf dist/*.tar.gz | head -20  # para ver os arquivos dentro do pacote
poetry publish
```
