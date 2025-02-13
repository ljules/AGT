"""
ASGI config for AGT project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
import CORE.routing # Import du fichier où on définit WebSockets

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AGT.settings')

#application = get_asgi_application()
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(CORE.routing.websocket_urlpatterns),
})