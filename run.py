import torch
import cv2
import pygame
import time
import numpy as np
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)


# Load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
model.classes = [0]  # Only detect 'person'

# Initialize Pygame for sound
pygame.mixer.init()
alert_sound = pygame.mixer.Sound("alert.mp3")

# Debounce variables
last_play_time = 0
cooldown = 3  # seconds

# Capture video
cap = cv2.VideoCapture(0)  # 0 for default webcam 

# Set up window and mouse callback
cv2.namedWindow("Detection")
drawing_points = []
polygon_defined = False

def mouse_callback(event, x, y, flags, param):
    global drawing_points, polygon_defined
    if event == cv2.EVENT_LBUTTONDOWN and not polygon_defined:
        drawing_points.append((x, y))

cv2.setMouseCallback("Detection", mouse_callback)

print(f"\n######################################################")
print(f"\nClick at least 3 time on camera screen to set polygon")
print(f'\nPress "ESC" to set polygon, the final point will be linked to first point')
print(f'\nPress "Space" to erase polygon')
print(f'\n"ESC" many times to exit')


print(f"\n######################################################")

while True:
    ret, frame = cap.read()
    if not ret:
        #print("Failed to grab frame")
        break

    # Inference
    results = model(frame)
    detections = results.xyxy[0]  # [x1, y1, x2, y2, conf, class]

    for *box, conf, cls in detections:
        if int(cls) != 0:
            continue

        x1, y1, x2, y2 = map(int, box)
        center_x = (x1 + x2) // 2

        # Check if person is inside defined polygon
        if polygon_defined and len(drawing_points) >= 3:
            inside = cv2.pointPolygonTest(np.array(drawing_points, np.int32), (center_x, y2), False) >= 0
            if inside and time.time() - last_play_time > cooldown:
                alert_sound.play()
                last_play_time = time.time()

        # Draw detection
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Draw region
    if not polygon_defined:
        for pt in drawing_points:
            cv2.circle(frame, pt, 5, (255, 0, 0), -1)
        for i in range(1, len(drawing_points)):
            cv2.line(frame, drawing_points[i - 1], drawing_points[i], (255, 0, 0), 2)
    elif len(drawing_points) >= 3:
        pts = np.array(drawing_points, np.int32).reshape((-1, 1, 2))
        cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 255), thickness=2)

    # Show frame
    cv2.imshow("Detection", frame)
    key = cv2.waitKey(1)
    if key == 27:  # ESC key
        if not polygon_defined and len(drawing_points) >= 3:
            polygon_defined = True
        else:
            break
    elif key == 32:  # SPACE key to reset region
        drawing_points = []
        polygon_defined = False

cap.release()
cv2.destroyAllWindows()
