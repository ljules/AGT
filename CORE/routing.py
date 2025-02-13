from django.urls import re_path
from CORE.consumers import CropProgressConsumer, ReadQRCodeConsumer

websocket_urlpatterns = [
    re_path(r'ws/crop_progress/$', CropProgressConsumer.as_asgi()),  # WebSocket pour le recadrage
    re_path(r'ws/read_qr_progress/$', ReadQRCodeConsumer.as_asgi()),  # WebSocket pour la lecture des QR Codes
]
