import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ProgressConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        print("✅ Client WebSocket connecté !")  # Ajoutez ce log pour déboguer
        await self.channel_layer.group_add("progress_updates", self.channel_name)
        print("✅ Client ajouté au groupe 'progress_updates' !")  # Ajoutez ce log pour débogue

    async def disconnect(self, close_code):
        print("❌ Client WebSocket déconnecté !")  # Ajoutez ce log pour déboguer
        await self.channel_layer.group_discard("progress_updates", self.channel_name)
        print("❌ Client retiré du groupe 'progress_updates' !")  # Ajoutez ce log pour débogue

    async def send_progress(self, event):
        """
        Envoie la progression au client via WebSocket.
        """
        #print("Envoi d'un message au client :", event)  # Ajoutez ce log pour déboguer
        await self.send(text_data=json.dumps({
            "task": event["task"],  # Identifiant de la tâche ("crop" ou "qr_code" ou "download")
            "progress": event["progress"],
            "message": event["message"]
        }))
