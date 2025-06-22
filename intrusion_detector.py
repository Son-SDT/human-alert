from shapely.geometry import Point, Polygon
import torch, cv2, time
import numpy as np
import threading, warnings
from playsound import playsound
from datetime import datetime, timezone
from send_email import send_to_outlook
warnings.filterwarnings("ignore", category=FutureWarning)


def isInside(points, centroid):
    polygon = Polygon(points)
    centroid = Point(centroid)
    return polygon.contains(centroid)


def send_outlook():
    send_to_outlook()

        
class YoloDetect:
    def __init__(self, detect_class="person", frame_width=1280, frame_height=720):
        self.detect_class = detect_class
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.conf_threshold = 0.5
        self.alert_outlook_each = 45  # seconds
        self.last_alert = None
        self.alert_active = False
        self.sound_thread = None

        # Load model from torch.hub
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        self.model.conf = self.conf_threshold
        self.model.classes = [0]  # Only detect 'person'
        self.classnames = self.model.names

    def draw_prediction(self, frame, x1, y1, x2, y2, points):
    #    label = self.classnames[class_id]
        color = (0, 255, 0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    #    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        #centroid = ((x1 + x2) // 2, y2)
        centroid = ((x1 + x2) // 2, (y1 + y2) // 2)
        cv2.circle(frame, centroid, 5, color, -1)

        if isInside(points, centroid):
            frame = self.alert(frame)

        return isInside(points, centroid)
    def play_sound_loop(self, path):
        while self.alert_active:
            try:
                playsound(path)          # 🔊 Play sound immediately
                time.sleep(2)      
            except Exception as e:
                print(f"Error playing sound: {e}")
                break

    def start_sound_alert(self, path="./alert.mp3"):
        if not self.alert_active:
            self.alert_active = True
            self.sound_thread = threading.Thread(target=self.play_sound_loop, args=(path,), daemon=True)
            self.sound_thread.start()

    def stop_sound_alert(self):
        self.alert_active = False
    def alert(self, frame):
        cv2.putText(frame, "INTRUSION ALERT", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        self.start_sound_alert("./alert.mp3")
        now = datetime.now(timezone.utc)
        if (self.last_alert is None) or ((now - self.last_alert).total_seconds() > self.alert_outlook_each):
            self.last_alert = now
            cv2.imwrite("alert.png", cv2.resize(frame, dsize=None, fx=0.8, fy=0.8))
            thread = threading.Thread(target=send_to_outlook)
            thread.start()
        return frame

    def detect(self, frame, points):
        # Inference
        results = self.model(frame)
        detections = results.xyxy[0]  # tensor [x1, y1, x2, y2, conf, class]

        for *xyxy, conf, cls in detections:
            class_id = int(cls.item())
            label = self.classnames[class_id]
            if label != self.detect_class:
                continue

            x1, y1, x2, y2 = map(int, xyxy)
            self.draw_prediction(frame, x1, y1, x2, y2, points)

        return frame
