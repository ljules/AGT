import json
import time
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from CORE.models import Photo
from CORE.utils.crop_on_face import crop_on_face


# Progression pour le rognage de toutes les photos :
# --------------------------------------------------
class CropProgressConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def receive(self, text_data):
        photos = Photo.objects.all()
        total = len(photos)
        count = 0

        for photo in photos:
            crop_on_face(photo)
            count += 1
            progress = int((count / total) * 100)

            # Envoi du pourcentage et de l’état actuel
            self.send(text_data=json.dumps({
                'progress': progress,
                'message': f"{count}/{total} fichiers traités"
            }))

            #time.sleep(0.5)  # Pour simuler un traitement progressif

        self.send(text_data=json.dumps({'progress': 100, 'message': "Recadrage terminé !"}))


# Progression pour la lecture du QR Code de toutes les photos :
# -------------------------------------------------------------
class ReadQRCodeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        # Envoie le vrai channel_name au client
        await self.send(text_data=json.dumps({"channel_name": self.channel_name}))

    async def disconnect(self, close_code):
        pass  # Pas d'action spécifique nécessaire à la déconnexion

    async def send_progress(self, event):
        """
        Envoie la progression de lecture des QR Codes au client via WebSocket.
        """
        await self.send(text_data=json.dumps({
            "progress": event["progress"],
            "message": event["message"]
        }))