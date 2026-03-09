import cv2

stream_url = "http://192.168.70.149:8080/video"
cap = cv2.VideoCapture(stream_url)

while True:
    ret, frame = cap.read()
    if ret:
        cv2.imshow('Phone Camera', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()