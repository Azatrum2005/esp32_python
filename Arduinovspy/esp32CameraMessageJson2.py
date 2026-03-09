import websockets
import asyncio
import cv2
import numpy as np
import mediapipe as mp
import threading
import queue
import json
import time
import math 

class ESP32VideoStreamClient:
    def __init__(self, websocket_url="ws://your_esp32_ip:81", stream_url="http://your_esp32_ip/stream"):
        self.websocket_url = websocket_url
        self.stream_url = stream_url
        self.websocket = None
        self.frame_queue = queue.Queue(maxsize=10)
        self.stop_event = threading.Event()
        self.loop = asyncio.get_event_loop()
        self.lock = threading.Lock()

    def video_capture_thread(self):
        """Thread for capturing video frames"""
        cap = cv2.VideoCapture(self.stream_url)
        try:
            while not self.stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    print("Error: Could not read frame")
                    break
                
                try:
                    if self.frame_queue.qsize() < 10:
                        self.frame_queue.put_nowait(frame)
                    else:
                        # Drop old frames when queue is full
                        _ = self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(frame)
                except queue.Full:
                    pass
                except queue.Empty:
                    pass
        finally:
            cap.release()
            self.stop_event.set()
    
    def rotate(self,img, angle, rotPoint=None,scale=1):
        (height,width) = img.shape[:2]
        if rotPoint is None:
            rotPoint = (width//2,height//2)
        
        rotMat = cv2.getRotationMatrix2D(rotPoint, angle, scale)
        dimensions = (width,height)
        return cv2.warpAffine(img, rotMat, dimensions)

    def display_thread(self):
        """Thread for displaying video frames"""
        ct,pt=0,0
        self.dx,self.dy=0,0
        mpface=mp.solutions.face_detection
        face=mpface.FaceDetection(min_detection_confidence=0.7)
        # mpdraw=mp.solutions.drawing_utils
        while not self.stop_event.is_set():
            self.d=0
            try:
                frame = self.frame_queue.get(timeout=0.5)
                img = self.rotate(frame,180,None, 1)
                imgrgb=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
                results=face.process(imgrgb)
                if results.detections:
                    self.d=1
                    for id,d in enumerate(results.detections):
                        h,w,c=img.shape
                        #mpdraw.draw_detection(img,d)
                        s=d.score[0]
                        v=d.location_data.relative_bounding_box
                        co={1:int(v.xmin*w),2:int(v.ymin*h),3:int(v.width*w),4:int(v.height*h)}
                        cv2.rectangle(img,(co[1],co[2]),(co[3]+co[1],co[4]+co[2]),(200,200,200),2)
                        cv2.line(img,(co[1]-5,co[2]-5),(co[1]-5,co[2]+30),(0,0,0),5)
                        cv2.line(img,(co[1]-5,co[2]-5),(co[1]+50,co[2]-5),(0,0,0),5)
                        cv2.line(img,(co[1]+co[3]+5,co[2]+co[4]+5),(co[1]+co[3]+5,co[2]+co[4]-30),(0,0,0),5)
                        cv2.line(img,(co[1]+co[3]+5,co[2]+co[4]+5),(co[1]+co[3]-50,co[2]+co[4]+5),(0,0,0),5)
                        cv2.putText(img,str(math.floor(s*100))+"%",(co[1],co[2]-13),cv2.FONT_HERSHEY_COMPLEX_SMALL,1,(0,200,0),2)
                        midp=(co[1]+ int(co[3]/2),co[2]+int(co[4]/2))
                        # cv.circle(img,midp,3,(0,0,0),cv.FILLED)
                        self.dx=midp[0]-w//2
                        self.dy=midp[1]-h//2
                        # img=cv.cvtColor(img,cv.COLOR_BGR2GRAY)
                        # imgs=img[midp[1]-200:midp[1]+100,midp[0]-150:midp[0]+150]
                ct=time.time()
                fps=1/(ct-pt)
                pt=ct
                cv2.putText(img,"fps:"+str(int(fps)),(10,30),cv2.FONT_HERSHEY_COMPLEX_SMALL,1,(0,0,0),1)
                cv2.imshow("Facetracking",img)
                key = cv2.waitKey(10) & 0xFF
                
                # if key == ord('q'):
                #     self.stop_event.set()
                    
                self.frame_queue.task_done()
            except queue.Empty:
                continue
        
        cv2.destroyAllWindows()

    async def connect_websocket(self):
        """Connect to the ESP32 WebSocket server"""
        try:
            self.websocket = await websockets.connect(
                self.websocket_url,
                ping_interval=10,
                ping_timeout=5
            )
            print("Connected to ESP32 WebSocket server")
            return True
        except Exception as e:
            print(f"WebSocket connection failed: {e}")
            return False
    
    async def send_message(self, action, state):
        """Send LED control command"""
        if self.websocket:
            try:
                await self.websocket.send(json.dumps({
                    "action": action, 
                    "content": state
                }))
                print(f"Message Sent: {state}")
            except Exception as e:
                print(f"Error sending Message: {e}")

    def send_messages(self):
        # l=0
        asyncio.run_coroutine_threadsafe(self.send_message("pid",{"P":0.5,"I":0.008,"D":0.05,"sp":0}), self.loop)
        while not self.stop_event.is_set() and self.websocket:
            # l=not l
            try:
                frame2 = np.zeros((200,200))
                cv2.putText(frame2,"Send Message",(10,100),cv2.FONT_HERSHEY_COMPLEX_SMALL,1,(250,250,250),1)
                cv2.imshow('Message', frame2)
                if self.d==1:
                    asyncio.run_coroutine_threadsafe(self.send_message("dx",self.dx),self.loop)
                    time.sleep(0.01)
                    asyncio.run_coroutine_threadsafe(self.send_message("dy",self.dy),self.loop)
                else:
                    asyncio.run_coroutine_threadsafe(self.send_message("dx",0),self.loop)
                    time.sleep(0.01)
                    asyncio.run_coroutine_threadsafe(self.send_message("dy",0),self.loop)
                key2 = cv2.waitKey(20) & 0xFF
                if key2 == ord('q'):
                    self.stop_event.set()
                # elif key2 == ord('n') or l==1:
                #     asyncio.run_coroutine_threadsafe(self.send_message("led","on"), self.loop)
                # elif key2 == ord('f') or l==1:
                #     asyncio.run_coroutine_threadsafe(self.send_message("led","off"), self.loop)
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosed:
                print("WebSocket connection closed")
                self.stop_event.set()
                break
            except Exception as e:
                print(f"Error receiving message: {e}")
                self.stop_event.set()
                break

    async def receive_messages(self):
        """Continuously receive messages from WebSocket"""
        while not self.stop_event.is_set() and self.websocket:
            try:
                message = await asyncio.wait_for(
                    self.websocket.recv(),
                    timeout=1.0
                )
                data = json.loads(message)
                print(f"Received message: {data}")
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosed:
                print("WebSocket connection closed")
                self.stop_event.set()
                break
            except Exception as e:
                print(f"Error receiving message: {e}")
                self.stop_event.set()
                break

    async def run(self):
        """Main async method to manage connections and threads"""
        if not await self.connect_websocket():
            return

        # Start threads
        capture_thread = threading.Thread(target=self.video_capture_thread)
        display_thread = threading.Thread(target=self.display_thread)
        send_thread = threading.Thread(target=self.send_messages)
        capture_thread.start()
        display_thread.start()
        send_thread.start()

        # Start WebSocket message receiver
        receiver_task = asyncio.create_task(self.receive_messages())

        # Monitor stop event and threads
        while not self.stop_event.is_set():
            await asyncio.sleep(0.5)
            if not capture_thread.is_alive() or not display_thread.is_alive():
                self.stop_event.set()

        await self.close()
        receiver_task.cancel()
        try:
            await receiver_task
        except asyncio.CancelledError:
            pass

        capture_thread.join(timeout=1)
        display_thread.join(timeout=1)
        send_thread.join(timeout=1)

    async def close(self):
        """Cleanup resources"""
        if self.websocket and not self.websocket.close:
            await self.websocket.close()
        self.stop_event.set()

async def main():
    client = ESP32VideoStreamClient(
        stream_url="http://192.168.1.100/stream",
        websocket_url="ws://192.168.1.100:81"
    )
    
    try:
        await client.run()
    except KeyboardInterrupt:
        print("Shutting down...")
        await client.close()
    finally:
        await client.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
