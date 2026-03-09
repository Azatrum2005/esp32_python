import cv2
import numpy as np
import requests
import threading
from queue import Queue
import time
import websocket
import json

class ESP32Controller:
    def __init__(self, ip_address='192.168.70.124', port=80, ws_port=81):
        # Camera stream setup
        self.stream_url = f'http://{ip_address}:{port}/stream'
        self.frame_queue = Queue(maxsize=32)
        self.stop_event = threading.Event()
        self.connected = False
        
        # WebSocket setup
        websocket.enableTrace(True)  # Enable WebSocket debug traces
        self.ws_url = f'ws://{ip_address}:{ws_port}/'
        self.ws = None
        self.ws_thread = None
        self.setup_websocket()
        
    def on_ws_message(self, ws, message):
        """Called when a message is received from ESP32"""
        try:
            print(f"Received from ESP32: {message}")
            # You can add specific handlers for different messages here
            if message == "led on":
                print("LED has been turned on")
                # time.sleep(1)
            elif message == "led off":
                print("LED has been turned off")
                # time.sleep(1)
            # Add more handlers as needed
            
        except Exception as e:
            print(f"Error processing message: {e}")

    def on_ws_error(self, ws, error):
        """Called when a WebSocket error occurs"""
        print(f"WebSocket error: {error}")

    def on_ws_close(self, ws, close_status_code, close_msg):
        """Called when WebSocket connection closes"""
        print("WebSocket connection closed")
        self.setup_websocket()

    def on_ws_open(self, ws):
        """Called when WebSocket connection opens"""
        print("WebSocket connection opened")
        
    def setup_websocket(self):
        """Initialize WebSocket connection with callbacks"""
        try:
            # Create WebSocket app with callbacks
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                on_message=self.on_ws_message,
                on_error=self.on_ws_error,
                on_close=self.on_ws_close,
                on_open=self.on_ws_open
            )
            
            # Run WebSocket client in a separate thread
            self.ws_thread = threading.Thread(target=self.ws.run_forever)
            self.ws_thread.daemon = True
            self.ws_thread.start()
            
            # Wait a bit for connection
            time.sleep(1)
            print("WebSocket setup completed")
            
        except Exception as e:
            print(f"WebSocket setup failed: {e}")
            
    def send_ws_message(self, message):
        """Send message to ESP32"""
        try:
            if self.ws and self.ws.sock and self.ws.sock.connected:
                self.ws.send(message)
                print(f"Sent to ESP32: {message}")
            else:
                print("WebSocket not connected")
                self.setup_websocket()
        except Exception as e:
            print(f"Error sending message: {e}")
            self.setup_websocket()
            
    def led_on(self):
        """Turn LED on"""
        self.send_ws_message('on')
            
    def led_off(self):
        """Turn LED off"""
        self.send_ws_message('off')
    
    def _stream_reader(self):
        """Read camera stream in background thread"""
        try:
            print(f"Connecting to camera stream at {self.stream_url}")
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
                    jpg = bytes_buffer[a:b+2]
                    bytes_buffer = bytes_buffer[b+2:]
                    frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), 
                                       cv2.IMREAD_COLOR)
                    
                    if frame is not None and not self.frame_queue.full():
                        self.frame_queue.put(frame)
                        
        except Exception as e:
            print(f"Stream error: {e}")
        finally:
            self.connected = False
            
    def start(self):
        """Start the camera stream"""
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._stream_reader)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        """Stop the camera stream and close connections"""
        self.stop_event.set()
        if hasattr(self, 'thread'):
            self.thread.join()
        if self.ws:
            self.ws.close()
        if self.ws_thread:
            self.ws_thread.join(timeout=1)
            
    def read(self, timeout=1.0):
        """Read a frame from the camera"""
        if not self.connected:
            return False, None
        try:
            frame = self.frame_queue.get(timeout=timeout)
            return True, frame
        except:
            return False, None

def main():
    # Replace with your ESP32's IP address
    ESP32_IP = "192.168.70.124"  # Change this!
    
    # Create ESP32 controller
    esp32 = ESP32Controller(ip_address=ESP32_IP)
    
    try:
        # Start camera stream
        esp32.start()
        time.sleep(1)  # Wait for connection
        
        if not esp32.connected:
            print("Failed to connect to camera stream")
            return
            
        while True:
            ret, frame = esp32.read()
            
            if ret:
                # Show frame
                cv2.imshow('ESP32 Camera Stream', frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('n'):  # Press 'n' for LED ON
                    esp32.led_on()
                elif key == ord('f'):  # Press 'f' for LED OFF
                    esp32.led_off()
            else:
                print("No frame received")
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        esp32.stop()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()