import websockets
import asyncio
import numpy as np
import cv2 as cv
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
        self.last_sent = 0
        self.command_cooldown = 0.01

    def video_capture_thread(self):
        """Thread for capturing video frames."""
        cap = cv.VideoCapture(self.stream_url)

        while not self.stop_event.is_set():
            ret, frame = cap.read()

            if not ret:
                print("Error: Could not read frame")
                break

            try:
                if not self.frame_queue.full():
                    self.frame_queue.put_nowait(frame)
            except queue.Full:
                pass

        cap.release()

    def display_thread(self, loop):
        """Thread for displaying video frames and handling user input."""
        ct,pt,distancex,f1,f2,f3=0,0,0,0,0,0
        mpface=mp.solutions.face_detection
        face=mpface.FaceDetection(min_detection_confidence=0.7)
        mpdraw=mp.solutions.drawing_utils
        while not self.stop_event.is_set():
            try:
                frame = self.frame_queue.get(timeout=1)
                # M= cv.getRotationMatrix2D((320,240),90, 1.0)
                # frame = cv.warpAffine(frame, M, (640, 480))
                img=cv.flip(frame,1)
                img =cv.rotate(img, cv.ROTATE_90_CLOCKWISE)
                imgrgb=cv.cvtColor(img,cv.COLOR_BGR2RGB)
                results=face.process(imgrgb)
                
                if results.detections:
                    for id,d in enumerate(results.detections):
                        h,w,c=img.shape
                        s=d.score[0]
                        v=d.location_data.relative_bounding_box
                        co={1:int(v.xmin*w),2:int(v.ymin*h),3:int(v.width*w),4:int(v.height*h)}
                        cv.rectangle(img,(co[1],co[2]),(co[3]+co[1],co[4]+co[2]),(200,200,200),2)
                        midp=(co[1]+ int(co[3]/2),co[2]+int(co[4]/2))
                        distancex=midp[0]-w//2
                        current_time = time.time()
                        if True:#current_time - self.last_sent > self.command_cooldown:
                            if distancex<=50 and distancex>=-50 and f1==0:
                                asyncio.run_coroutine_threadsafe(self.send_message("input",0), loop)
                                asyncio.run_coroutine_threadsafe(self.send_message("move",1), loop)
                                f1,f2,f3=1,0,0
                                # self.last_sent = current_time
                            elif distancex<-50 and f2==0:
                                asyncio.run_coroutine_threadsafe(self.send_message("move",0), loop)
                                asyncio.run_coroutine_threadsafe(self.send_message("input",4), loop)
                                f1,f2,f3=0,1,0
                                # self.last_sent = current_time
                            elif distancex>50 and f3==0:
                                asyncio.run_coroutine_threadsafe(self.send_message("move",0), loop)
                                asyncio.run_coroutine_threadsafe(self.send_message("input",3), loop)
                                f1,f2,f3=0,0,1
                                # self.last_sent = current_time

                ct=time.time()
                fps=1/(ct-pt)
                pt=ct
                cv.putText(img,"fps:"+str(int(fps)),(10,30),cv.FONT_HERSHEY_COMPLEX_SMALL,1,(0,0,0),1)
                cv.imshow("facetracking",img)

                key = cv.waitKey(10) & 0xFF
                if key == ord('q'):
                    self.stop_event.set()
            except queue.Empty:
                continue

        cv.destroyAllWindows()

    async def connect_websocket(self):
        """Connect to the ESP32 WebSocket server."""
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            print("Connected to ESP32 WebSocket")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    async def send_message(self,action,message):
        """Send a chat message to the server"""
        if self.websocket:
            try:
                await self.websocket.send(json.dumps({"action": f"{action}", "content":message}))
            except Exception as e:
                print(f"Error sending message: {e}")

    async def receive_messages(self):
        """Receive messages from the WebSocket server."""
        while not self.stop_event.is_set():
            try:
                message = await self.websocket.recv()
                data = json.loads(message)
                print(f"Received: {data}")
            except websockets.exceptions.ConnectionClosed:
                print("WebSocket connection closed")
                await self.close()
                await self.connect_websocket()
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    async def close(self):
        """Close the WebSocket connection."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

    async def run(self):
        """Main method to start threads and async loop."""
        # Start video capture thread
        capture_thread = threading.Thread(target=self.video_capture_thread)
        capture_thread.start()

        # Start display thread
        loop = asyncio.get_event_loop()
        display_thread = threading.Thread(target=self.display_thread, args=(loop,))
        display_thread.start()

        # Start receiving messages
        try:
            await self.receive_messages()
        except asyncio.CancelledError:
            pass

        # Wait for threads to finish
        capture_thread.join()
        display_thread.join()


async def main():
    """Run the video stream client."""
    client = ESP32VideoStreamClient(
        stream_url="http://192.168.70.124/stream",
        websocket_url="ws://192.168.70.124:81"
    )

    if await client.connect_websocket():
        try:
            await client.run()
        finally:
            await client.close()


if __name__ == "__main__":
    asyncio.run(main())