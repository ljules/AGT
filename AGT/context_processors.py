######################################################
#                                                    #
#   FICHIER DE CONTEXT PROCESSOR DE L'APPLICATION    #
#                                                    #
######################################################

# Description et remarques :
# --------------------------
# Ce fichier permet de rendre disponible les constantes du fichier : constants.py
# Pour que ce fichier soit pris en considération par Django, son nom doit être
# renseigné dans le fichier settings.py dans la liste TEMPLATES.

from django.conf import settings
from django.template.context_processors import csrf

def global_settings(request):
    return {
        "SITE_NAME": settings.SITE_NAME,
    }

def csrf_token_processor(request):
    return {'csrf_token': csrf(request)['csrf_token']}

def media_url_processor(request):
    """
    Ajoute MEDIA_URL au contexte global.
    """
    return {
        'MEDIA_URL': settings.MEDIA_URL,
    }


def previous_url(request):
    """
    Permet d'accéder à l'url de la page précédente.
    """
    return {'previous_url': request.META.get('HTTP_REFERER', '')}
