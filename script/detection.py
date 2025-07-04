import warnings
from shapely.geometry import Point, Polygon
from ultralytics import YOLO
from script.notify import Notification

warnings.filterwarnings("ignore", category=FutureWarning)


class YoloDetect:
    ALERT_COLOR = (0, 255, 255)
    DETECTION_COLOR = (0, 255, 0)
    THRESHOLD = 0.5
    SOUND_DELAY = 0.5
    MAIL_DELAY = 45
    IMAGE_RESIZE_SCALE = 0.8

    def __init__(
        self,
        target: str = "person",
    ) -> None:
        self.target = target
        self.notify = Notification()

        try:
            self.model = YOLO("yolov5s.pt")
            self.model.conf = self.THRESHOLD
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")

    def __alert(self, cv2, frame) -> None:
        # draw notification on frame
        cv2.putText(
            frame,
            "Intrusion Alert",
            (10, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            self.ALERT_COLOR,
            2,
        )

        # redraw image for alert
        if self.notify.canSend():
            cv2.imwrite(
                "../asset/alert.png",
                cv2.resize(
                    frame,
                    dsize=None,
                    fx=self.IMAGE_RESIZE_SCALE,
                    fy=self.IMAGE_RESIZE_SCALE,
                ),
            )

        # toggle alert system
        self.notify.toggleAlertSystem()

    def __detected(self, cv2, frame, xyxy, points: list[list[int]]) -> bool:
        x1, y1, x2, y2 = map(int, xyxy)
        centroid = ((x1 + x2) // 2, (y1 + y2) // 2)

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            self.DETECTION_COLOR,
            2,
        )
        cv2.circle(frame, centroid, 5, self.DETECTION_COLOR, -1)

        polygon = Polygon(points)

        return polygon.contains(Point(centroid))

    def startDetect(self, cv2, frame, points: list[list[int]]) -> None:
        detections = self.model(frame)[0]  # call predict() under with default value
        for box in detections.boxes:
            classId = int(box.cls.item())
            label = self.model.names[classId]
            if label != self.target:
                continue

            if self.__detected(cv2, frame, box.xyxy[0].tolist(), points):
                self.__alert(cv2, frame)

    def stopDetect(self) -> None:
        self.notify.isActive = False
