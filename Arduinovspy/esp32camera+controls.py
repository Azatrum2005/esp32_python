# import cv2
# import numpy as np
# import requests
# import threading
# from queue import Queue
# import time
# import websocket
# import json

# class ESP32Controller:
#     def __init__(self, ip_address='192.168.1.100', port=80, ws_port=81):
#         # Camera stream setup
#         self.stream_url = f'http://{ip_address}:{port}/stream'
#         self.frame_queue = Queue(maxsize=32)
#         self.stop_event = threading.Event()
#         self.connected = False
        
#         # WebSocket setup for LED control
#         self.ws_url = f'ws://{ip_address}:{ws_port}/'
#         self.ws = None
#         self.setup_websocket()
        
#     def setup_websocket(self):
#         """Initialize WebSocket connection"""
#         try:
#             self.ws = websocket.WebSocket()
#             self.ws.connect(self.ws_url)
#             print("WebSocket connected successfully")
#         except Exception as e:
#             print(f"WebSocket connection failed: {e}")
            
#     def led_on(self):
#         """Turn LED on"""
#         try:
#             if self.ws:
#                 self.ws.send('on')
#                 print("LED ON command sent")
#             else:
#                 print("WebSocket not connected")
#         except Exception as e:
#             print(f"Error sending LED ON command: {e}")
            
#     def led_off(self):
#         """Turn LED off"""
#         try:
#             if self.ws:
#                 self.ws.send('off')
#                 print("LED OFF command sent")
#             else:
#                 print("WebSocket not connected")
#         except Exception as e:
#             print(f"Error sending LED OFF command: {e}")
    
#     def _stream_reader(self):
#         """Read camera stream in background thread"""
#         try:
#             print(f"Connecting to camera stream at {self.stream_url}")
#             response = requests.get(self.stream_url, stream=True, timeout=5)
#             if response.status_code != 200:
#                 print(f"Failed to connect. Status code: {response.status_code}")
#                 return
                
#             print("Camera stream connected successfully!")
#             self.connected = True
            
#             bytes_buffer = bytes()
#             for chunk in response.iter_content(chunk_size=1024):
#                 if self.stop_event.is_set():
#                     break
                    
#                 bytes_buffer += chunk
#                 a = bytes_buffer.find(b'\xff\xd8')
#                 b = bytes_buffer.find(b'\xff\xd9')
                
#                 if a != -1 and b != -1:
#                     jpg = bytes_buffer[a:b+2]
#                     bytes_buffer = bytes_buffer[b+2:]
#                     frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), 
#                                        cv2.IMREAD_COLOR)
                    
#                     if frame is not None and not self.frame_queue.full():
#                         self.frame_queue.put(frame)
                        
#         except Exception as e:
#             print(f"Stream error: {e}")
#         finally:
#             self.connected = False
            
#     def start(self):
#         """Start the camera stream"""
#         self.stop_event.clear()
#         self.thread = threading.Thread(target=self._stream_reader)
#         self.thread.daemon = True
#         self.thread.start()
        
#     def stop(self):
#         """Stop the camera stream and close connections"""
#         self.stop_event.set()
#         if hasattr(self, 'thread'):
#             self.thread.join()
#         if self.ws:
#             self.ws.close()
            
#     def read(self, timeout=1.0):
#         """Read a frame from the camera"""
#         if not self.connected:
#             return False, None
#         try:
#             frame = self.frame_queue.get(timeout=timeout)
#             return True, frame
#         except:
#             return False, None

# def main():
#     # Replace with your ESP32's IP address
#     ESP32_IP = "192.168.1.100"  # Change this!
    
#     # Create ESP32 controller
#     esp32 = ESP32Controller(ip_address=ESP32_IP)
    
#     try:
#         # Start camera stream
#         esp32.start()
#         time.sleep(1)  # Wait for connection
        
#         if not esp32.connected:
#             print("Failed to connect to camera stream")
#             return
            
#         while True:
#             ret, frame = esp32.read()
#             # print(frame.shape)
#             # frame=np.zeros((1,1,3))
#             if ret:
#                 # Show frame
#                 cv2.imshow('ESP32 Camera Stream', frame)
                
#                 # Handle keyboard input
#                 key = cv2.waitKey(1) & 0xFF
#                 if key == ord('q'):
#                     break
#                 elif key == ord('n'):  # Press 'n' for LED ON
#                     esp32.led_on()
#                 elif key == ord('f'):  # Press 'f' for LED OFF
#                     esp32.led_off()
#             else:
#                 print("No frame received")
#                 time.sleep(1)
                
#     except KeyboardInterrupt:
#         print("\nStopping...")
#     finally:
#         esp32.stop()
#         cv2.destroyAllWindows()

# if __name__ == '__main__':
#     main()

import cv2
import numpy as np
import requests
import threading
from queue import Queue
import time
import asyncio
import websockets

class ESP32Controller:
    def __init__(self, ip_address='192.168.70.150', port=80, ws_port=81):
        self.stream_url = f'http://{ip_address}:{port}/stream'
        self.frame_queue = Queue(maxsize=32)
        self.stop_event = threading.Event()
        self.connected = False

        self.ws_uri = f'ws://{ip_address}:{ws_port}/'
        self.ws = None
        self.loop = asyncio.get_event_loop()
        self.ws_lock = asyncio.Lock()

    def _stream_reader(self):
        print(f"Connecting to camera stream at {self.stream_url}")
        try:
            response = requests.get(self.stream_url, stream=True, timeout=5)
            if response.status_code != 200:
                print(f"Failed to connect. Status code: {response.status_code}")
                return

            print("Camera stream connected successfully!")
            self.connected = True
            bytes_buffer = bytes()

            for chunk in response.iter_content(chunk_size=1024):
                if self.stop_event.is_set():
                    break

                bytes_buffer += chunk
                a = bytes_buffer.find(b'\xff\xd8')
                b = bytes_buffer.find(b'\xff\xd9')

                if a != -1 and b != -1:
                    jpg = bytes_buffer[a:b + 2]
                    bytes_buffer = bytes_buffer[b + 2:]
                    frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8),
                                          cv2.IMREAD_COLOR)
                    if frame is not None and not self.frame_queue.full():
                        self.frame_queue.put(frame)

        except Exception as e:
            print(f"Stream error: {e}")
        finally:
            self.connected = False

    def start(self):
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._stream_reader)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if hasattr(self, 'thread'):
            self.thread.join()

    def read(self, timeout=1.0):
        if not self.connected:
            return False, None
        try:
            frame = self.frame_queue.get(timeout=timeout)
            return True, frame
        except:
            return False, None

    async def _led_send(self, command: str):
        async with self.ws_lock:
            if not self.ws:
                self.ws = await websockets.connect(self.ws_uri)
                print("WebSocket connected successfully (async)")

            try:
                await self.ws.send(command)
                print(f"LED {command.upper()} command sent")
            except Exception as e:
                print(f"Error sending LED command: {e}")

    def led_on(self):
        asyncio.run_coroutine_threadsafe(self._led_send('on'), self.loop)

    def led_off(self):
        asyncio.run_coroutine_threadsafe(self._led_send('off'), self.loop)

    def close_ws(self):
        if self.ws:
            self.loop.run_until_complete(self.ws.close())

def main():
    ESP32_IP = "192.168.70.150"  # Change this!
    esp32 = ESP32Controller(ip_address=ESP32_IP)
    try:
        esp32.start()
        time.sleep(1)

        if not esp32.connected:
            print("Failed to connect to camera stream")
            return

        while True:
            ret, frame = esp32.read()
            if ret:
                cv2.imshow('ESP32 Camera Stream', frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('n'):
                    esp32.led_on()
                elif key == ord('f'):
                    esp32.led_off()
            else:
                print("No frame received")
                time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        esp32.stop()
        esp32.close_ws()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
