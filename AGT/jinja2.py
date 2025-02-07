from jinja2 import Environment
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
#from django.template.context_processors import csrf

from AGT import settings


def environment(**options):
    """
    Configure l'environnement Jinja2 pour Django.
    """
    # Crée l'environnement Jinja2
    env = Environment(**options)

    # Ajouter des fonctions globales pour Jinja2
    env.globals.update({
        'static': staticfiles_storage.url,  # Utilisation de la fonction "static"
        'url': reverse,  # Génération des URLs Django
        'SITE_URL': settings.SITE_URL, # Récupération de la constante dans settings.py pour SITE_URL
        'SITE_NAME': settings.SITE_NAME,
        #'csrf_token': lambda request: csrf(request)['csrf_token'],  # Récupère le token
    })

    # Ajouter des filtres personnalisés (facultatif)
    env.filters['uppercase'] = lambda text: text.upper()  # Exemple : Filtre personnalisé pour mettre en majuscules

    return env
