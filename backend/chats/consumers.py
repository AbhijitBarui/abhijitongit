import json
from channels.generic.websocket import WebsocketConsumer

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]

        # Example static response; replace with AI/logic later
        response = f"You said: {message}"

        self.send(text_data=json.dumps({
            "message": response
        }))
