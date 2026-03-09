import cv2
import mediapipe as mp
import math
import numpy as np
import requests
from urllib.parse import urljoin
import threading
from queue import Queue
import time

class ESP32CameraStream:
    def __init__(self, ip_address='192.168.1.100', port=80, max_queue_size=32):
        self.stream_url = f'http://{ip_address}:{port}/stream'
        self.frame_queue = Queue(maxsize=max_queue_size)
        self.stop_event = threading.Event()
        self.latest_frame = None
        self.connected = False
        print(f"Attempting to connect to: {self.stream_url}")
        
    def _stream_reader(self):
        bytes_buffer = bytes()
        frames_received = 0
        
        try:
            print(f"Testing connection to {self.stream_url}...")
            # First test if we can connect
            response = requests.get(self.stream_url, stream=True, timeout=5)
            if response.status_code != 200:
                print(f"Failed to connect. Status code: {response.status_code}")
                return
                
            print("Connected successfully! Starting stream...")
            self.connected = True
            
            # Read stream content
            for chunk in response.iter_content(chunk_size=1024):
                if self.stop_event.is_set():
                    break
                    
                bytes_buffer += chunk
                a = bytes_buffer.find(b'\xff\xd8')  # JPEG start
                b = bytes_buffer.find(b'\xff\xd9')  # JPEG end
                
                if a != -1 and b != -1:
                    jpg = bytes_buffer[a:b+2]
                    bytes_buffer = bytes_buffer[b+2:]
                    
                    # Decode JPEG to numpy array
                    frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), 
                                       cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        frames_received += 1
                        if frames_received % 30 == 0:  # Log every 30 frames
                            print(f"Received {frames_received} frames")
                        
                        self.latest_frame = frame
                        if not self.frame_queue.full():
                            self.frame_queue.put(frame)
                    else:
                        print("Failed to decode frame")
                            
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: {e}")
            print("\nTroubleshooting steps:")
            print("1. Verify the ESP32's IP address is correct")
            print("2. Make sure ESP32 and computer are on the same network")
            print("3. Try accessing the stream in a web browser")
            print(f"4. Check if you can ping the ESP32: ping {self.stream_url.split('//')[1].split('/')[0]}")
        except requests.exceptions.Timeout:
            print("Connection timed out. ESP32 not responding")
        except Exception as e:
            print(f"Unexpected error in stream reader: {e}")
            import traceback
            traceback.print_exc()
            
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
        # except Exception as e:
        #     print(f"Error reading frame: {e}")
        #     return False, None

def main():
    # Replace with your ESP32's IP address
    ESP32_IP = "192.168.70.124"  # Change this to your ESP32's IP address!
    
    # Test connection first
    try:
        print(f"Testing connection to http://{ESP32_IP}...")
        response = requests.get(f"http://{ESP32_IP}", timeout=5)
        print(f"Connection test result: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to ESP32: {e}")
        return

    camera = ESP32CameraStream(ip_address=ESP32_IP)
    mpface=mp.solutions.face_detection
    face=mpface.FaceDetection(min_detection_confidence=0.7)
    mpdraw=mp.solutions.drawing_utils
    try:
        print("Starting camera stream...")
        camera.start()
        
        # Wait a bit for connection
        time.sleep(2)
        
        if not camera.connected:
            print("Failed to connect to camera stream")
            return
        fps=0   
        frame_count = 0
        start_time = time.time()
        
        while True:
            ret, frame = camera.read()
            img=cv2.flip(frame,1)
            if ret:
                frame_count += 1
                if frame_count % 30 == 0:  # Log FPS every 30 frames
                    elapsed_time = time.time() - start_time
                    fps = frame_count / elapsed_time
                    print(f"FPS: {fps:.2f}")
                # Process frame with OpenCV
                results=face.process(img)
                if results.detections:
                    for id,d in enumerate(results.detections):
                        h,w,c=img.shape
                        s=d.score[0] 
                        v=d.location_data.relative_bounding_box
                        co={1:int(v.xmin*w),2:int(v.ymin*h),3:int(v.width*w),4:int(v.height*h)}
                        cv2.rectangle(img,(co[1],co[2]),(co[3]+co[1],co[4]+co[2]),(200,200,200),2)
                        cv2.line(img,(co[1]-5,co[2]-5),(co[1]-5,co[2]+30),(0,0,0),5)
                        cv2.line(img,(co[1]-5,co[2]-5),(co[1]+50,co[2]-5),(0,0,0),5)
                        cv2.line(img,(co[1]+co[3]+5,co[2]+co[4]+5),(co[1]+co[3]+5,co[2]+co[4]-30),(0,0,0),5)
                        cv2.line(img,(co[1]+co[3]+5,co[2]+co[4]+5),(co[1]+co[3]-50,co[2]+co[4]+5),(0,0,0),5)
                        cv2.putText(img,str(math.floor(s*100))+"%",(co[1],co[2]-13),cv2.FONT_HERSHEY_COMPLEX_SMALL,1,(0,200,0),2)
                # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                cv2.putText(img,"fps:"+str(int(fps)),(10,30),cv2.FONT_HERSHEY_COMPLEX_SMALL,1,(0,0,0),1)
                cv2.imshow('ESP32 Camera Stream face tracking', img)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                print("No frame received, waiting...")
                time.sleep(1)
                    
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        camera.stop()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()