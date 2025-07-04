import torch, warnings
from shapely.geometry import Point, Polygon
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
            self.model = torch.hub.load(
                "ultralytics/yolov5", "yolov5s", pretrained=True
            )
            self.model.conf = self.THRESHOLD  # type: ignore[attr-defined]
            self.model.classes = [0]  # type: ignore[attr-defined]
        except Exception as e:
            raise e

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
                "../asset/alert.png", cv2.resize(frame, dsize=None, fx=0.8, fy=0.8)
            )

        # toggle alert system
        self.notify.toggleAlertSystem()

    def __detected(self, cv2, frame, inputs: list[int], points: list[int]) -> bool:
        x1, y1, x2, y2 = inputs
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
        centroid = Point(centroid)

        return polygon.contains(centroid)

    def startDetect(self, cv2, frame, points: list[int]) -> None:
        detections = self.model(frame).xyxy[0]  # type: ignore[attr-defined]
        for *xyxy, _, cls in detections:
            classId = int(cls.item())
            label = self.model.names[classId]  # type: ignore[attr-defined]
            if label != self.target:
                continue

            if self.__detected(cv2, frame, xyxy, points):
                self.__alert(cv2, frame)

    def stopDetect(self) -> None:
        self.notify.isActive = False
