import websockets
import asyncio
import json
import time
from openai import OpenAI
import datetime

client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = "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"
)

class ESP32WebSocketClient:
    def __init__(self, uri="ws://192.168.70.150:81"):
        self.uri = uri
        self.websocket = None
        
    async def connect(self):
        """Connect to the ESP32 WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.uri)
            print("Connected to ESP32")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
            
    async def send_name(self, name, client_number):
        """Send a name update to the server"""
        message = {
            "action": "send_name",
            "content": name,
            "number": client_number
        }
        await self.websocket.send(json.dumps(message))
        
    async def send_message(self, message, client_number):
        """Send a chat message to the server"""
        message = {
            "action": "send_message",
            "content": message,
            "number": client_number
        }
        await self.websocket.send(json.dumps(message))
    
    async def send_reply(self, message, client_number):
        """Send a formatted reply to the server"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = {
            "action": "send_reply",
            "content": message,
            "number": client_number,
            "metadata": {
                "timestamp": timestamp,
                "sender": "Azatrum",
                "messageType": "bot_reply"
            }
        }
        await self.websocket.send(json.dumps(formatted_message))
    # async def send_reply(self, message, client_number):
    #     """Send a chat message to the server"""
    #     message = {
    #         "action": "send_reply",
    #         "content": message,
    #         "number": client_number
    #     }
    #     await self.websocket.send(json.dumps(message))
    
    async def receive_messages(self):
        try:
            message = await self.websocket.recv()
            print(message)
            data = json.loads(message)
                
            if data["action"] == "update_message" and data['number'] != 1:
                if data['content'].lower() == "end convo":
                    await self.send_reply("Byeee!", 1)
                else:
                    # Show typing indicator on web client
                    typing_indicator = {
                        "action": "typing_status",
                        "content": "Azatrum is typing...",
                        "number": 1
                    }
                    clear_typing = {
                        "action": "typing_status",
                        "content": "",
                        "number": 1
                    }
                    await self.websocket.send(json.dumps(typing_indicator))

                    completion = client.chat.completions.create(
                        model="nvidia/llama-3.1-nemotron-70b-instruct",
                        messages=[{"role": "user", "content": f"{data['name']} said:" + data['content']}],
                        temperature=0.5,
                        top_p=1,
                        max_tokens=4096,
                        stream=True
                    )
                    
                    reply = ""
                    for text in completion:
                        if text.choices[0].delta.content is not None:
                            reply += text.choices[0].delta.content
                            # if "\n\n" not in text.choices[0].delta.content:
                            #     reply += text.choices[0].delta.content
                            # else:
                            #     await self.websocket.send(json.dumps(clear_typing))
                            #     await self.send_reply(reply, 1)
                            #     reply=""
                            #     await self.websocket.send(json.dumps(typing_indicator))
                    await self.websocket.send(json.dumps(clear_typing))
                    await self.send_reply(reply, 1)
                    # Clear typing indicator and send reply
                    # clear_typing = {
                    #     "action": "typing_status",
                    #     "content": "",
                    #     "number": 1
                    # }
                    # await self.websocket.send(json.dumps(clear_typing))     
    # async def receive_messages(self):
    #     """Listen for messages from the server"""
    #     try:
    #         # while True:
    #         message = await self.websocket.recv()
    #         data = json.loads(message)
                
    #         if data["action"] == "update_name":
    #             print(f"Client {data['number']} changed name to: {data['content']}")
               
    #         elif data["action"] == "update_message":
    #             print(f"Message from client {data['number']}: {data['content']}")
    #             # str=input("enter:")
    #             s=data['content']
    #             if s=="end convo" and data['number']!=1:
    #                 await self.send_reply("Byeee!", 1)
    #             elif data['number']!=1:
    #                 completion = client.chat.completions.create(
    #                 model="nvidia/llama-3.1-nemotron-70b-instruct",
    #                 messages=[{"role":"user","content":"in about or less than 200 words"+s}],
    #                 temperature=0.5,
    #                 top_p=1,
    #                 max_tokens=4096,
    #                 stream=True
    #                 )
    #                 reply=""
    #                 for text in completion:
    #                     if text.choices[0].delta.content is not None:
    #                         # print(text.choices[0].delta.content, end="")
    #                         reply=reply + text.choices[0].delta.content
    #                 await self.send_reply(reply, 1)
                    
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")
        except Exception as e:
            print(f"Error receiving message: {e}")
            
    async def close(self):
        """Close the WebSocket connection"""
        if self.websocket:
            print("closing websocket")
            await self.websocket.close()

# Example usage
async def main():
    # Create client instance
    client = ESP32WebSocketClient()
    
    # Connect to the server
    if await client.connect():
        # Start listening for messages in the background
        # receive_task = asyncio.create_task(client.receive_messages())
        # Example: Send a name update
        # await client.send_name("Alice", 2)
        # Example: Send a chat message
        # await client.send_message("Hello!", 2)
        await client.send_name("Azatrum", 1)
        # Keep the connection alive
        time.sleep(1)
        while True:
            try:
                await client.receive_messages()
                # await receive_task
            except KeyboardInterrupt:
                await client.close()

if __name__ == "__main__":
    asyncio.run(main())