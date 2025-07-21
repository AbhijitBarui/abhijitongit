import json
from channels.generic.websocket import WebsocketConsumer
from chats.agent.agent_mod_1 import handle_user_message

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]

        # Example static response; replace with AI/logic later
        response = handle_user_message(message) # f"You said: {message}"

        self.send(text_data=json.dumps({
            "message": response
        }))
