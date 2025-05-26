from django.urls import re_path
from CORE.consumers import ProgressConsumer

websocket_urlpatterns = [
    re_path(r'ws/progress/$', ProgressConsumer.as_asgi()),  # Un seul WebSocket pour les deux traitements
]
