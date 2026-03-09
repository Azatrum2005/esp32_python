import numpy as np
import mediapipe as mp
import time
import cv2 as cv
import math

stream_url = "http://192.168.70.149:8080/video"
cap = cv.VideoCapture(stream_url)
# cap=cv.VideoCapture(1)
cap.set(3,1280)
cap.set(4,720)
ct,pt=0,0
mpface=mp.solutions.face_detection
face=mpface.FaceDetection(min_detection_confidence=0.7)
mpdraw=mp.solutions.drawing_utils

while True:
    ret,frame=cap.read()
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
            cv.circle(img,midp,3,(0,0,0),cv.FILLED)
            # img=cv.cvtColor(img,cv.COLOR_BGR2GRAY)
            # print(img)
            # imgs=img[midp[1]-200:midp[1]+100,midp[0]-150:midp[0]+150]
    ct=time.time()
    fps=1/(ct-pt)
    pt=ct
    cv.putText(img,"fps:"+str(int(fps)),(10,30),cv.FONT_HERSHEY_COMPLEX_SMALL,1,(0,0,0),1)
    cv.imshow("facetracking",img)
    # cv.imshow("facesliced",imgs)
    key=cv.waitKey(1)
    if key==27:
        break