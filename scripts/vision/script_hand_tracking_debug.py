import cv2
from reality_mesa.vision.hand_tracking.hands_manager import HandsManager
from reality_mesa.vision.hand_tracking.debug_hand_tracking import debug_draw_hand_manager
width = 1920
height = 1080
fps = 30
hm = HandsManager(fps=fps,width=width,height=height)

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
cap.set(cv2.CAP_PROP_FPS, fps)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc(*'MJPG')) 

while True:
    ret, frame = cap.read()
    if not ret:
        break
    rgb = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
    hm.RunVision(rgb)
    debug_draw_hand_manager(rgb,hm)
    bgr = cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR)
    
    cv2.imshow("Tracked Hands", bgr)
    if cv2.waitKey(int(1000/fps)) & 0xFF == ord('q'):
        break