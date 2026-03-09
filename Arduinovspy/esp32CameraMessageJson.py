import websockets
import asyncio
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
        # asyncio.run_coroutine_threadsafe(self.send_message("pid",{"P":0.01,"I":0.001,"D":0.0}), loop)
        ct,pt,distancex=0,0,0
        mpface=mp.solutions.face_detection
        face=mpface.FaceDetection(min_detection_confidence=0.7)
        mpdraw=mp.solutions.drawing_utils
        while not self.stop_event.is_set():
            try:
                frame = self.frame_queue.get(timeout=1)
                # print(frame.shape)
                img=cv.flip(frame,1)
                imgrgb=cv.cvtColor(img,cv.COLOR_BGR2RGB)
                results=face.process(imgrgb)
                if results.detections:
                    for id,d in enumerate(results.detections):
                        h,w,c=img.shape
                        #mpdraw.draw_detection(img,d)
                        s=d.score[0]
                        v=d.location_data.relative_bounding_box
                        co={1:int(v.xmin*w),2:int(v.ymin*h),3:int(v.width*w),4:int(v.height*h)}
                        cv.rectangle(img,(co[1],co[2]),(co[3]+co[1],co[4]+co[2]),(200,200,200),2)
                        cv.line(img,(co[1]-5,co[2]-5),(co[1]-5,co[2]+30),(0,0,0),5)
                        cv.line(img,(co[1]-5,co[2]-5),(co[1]+50,co[2]-5),(0,0,0),5)
                        cv.line(img,(co[1]+co[3]+5,co[2]+co[4]+5),(co[1]+co[3]+5,co[2]+co[4]-30),(0,0,0),5)
                        cv.line(img,(co[1]+co[3]+5,co[2]+co[4]+5),(co[1]+co[3]-50,co[2]+co[4]+5),(0,0,0),5)
                        cv.putText(img,str(math.floor(s*100))+"%",(co[1],co[2]-13),cv.FONT_HERSHEY_COMPLEX_SMALL,1,(0,200,0),2)
                        midp=(co[1]+ int(co[3]/2),co[2]+int(co[4]/2))
                        # cv.circle(img,midp,3,(0,0,0),cv.FILLED)
                        # distancex=midp[0]-320
                        asyncio.run_coroutine_threadsafe(self.send_message("input",midp[0]), loop)
                        asyncio.run_coroutine_threadsafe(self.send_message("pid",{"P":0.0005,"I":0.0001,"D":0.0}), loop)
                        # img=cv.cvtColor(img,cv.COLOR_BGR2GRAY)
                        # print(img)
                        imgs=img[midp[1]-200:midp[1]+100,midp[0]-150:midp[0]+150]
                ct=time.time()
                fps=1/(ct-pt)
                pt=ct
                cv.putText(img,"fps:"+str(int(fps)),(10,30),cv.FONT_HERSHEY_COMPLEX_SMALL,1,(0,0,0),1)
                cv.imshow("facetracking",img)

                key = cv.waitKey(15) & 0xFF
                if key == ord('q'):
                    self.stop_event.set()
                elif key == ord('n'):
                    asyncio.run_coroutine_threadsafe(self.control_led('on'), loop)
                elif key == ord('f'):
                    asyncio.run_coroutine_threadsafe(self.control_led('off'), loop)
            except queue.Empty:
                continue

        cv.destroyAllWindows()

    async def connect_websocket(self):
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            print("Connected to ESP32 WebSocket")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    async def control_led(self, state):
        """Send LED control command."""
        if self.websocket:
            try:
                await self.websocket.send(json.dumps({"action": "led", "content": state}))
            except Exception as e:
                print(f"Error sending LED command: {e}")
    
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
                break
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
