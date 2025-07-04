import cv2
import numpy as np
from imutils.video import VideoStream
from script.detection import YoloDetect


class IntrusionDetectionApp:
    def __init__(self, receivers: list[str], camera: int = 0) -> None:
        self.points = []
        self.video = VideoStream(src=camera)
        self.model = None
        self.receivers = receivers

    def click(self, event: int, x: int, y: int, _, param) -> None:
        if event == cv2.EVENT_LBUTTONDOWN:
            self.points.append([x, y])

    def startCamera(self) -> None:
        try:
            self.video.start()
        except Exception as e:
            raise e

    def drawDetectingArea(self, frame, points) -> np.ndarray:
        for p in points:
            frame = cv2.circle(frame, (p[0], p[1]), 5, (0, 0, 255), -1)
        if len(points) > 1:
            frame = cv2.polylines(
                frame,
                [np.array(points, dtype=np.int32)],
                False,
                (255, 0, 0),
                thickness=2,
            )
        return frame

    def close(self) -> None:
        if self.video:
            self.video.stop()
        if self.model:
            self.model.stopDetect()
        cv2.destroyAllWindows()

    def run(self) -> None:
        try:
            self.startCamera()
            self.model = YoloDetect()
            if not self.model:
                raise Exception("Unable to initiate model")

            self.model.notify.RECEIVERS = self.receivers
            detecting = False
            windowName = "Intrusion Warning"
            cv2.namedWindow(windowName)
            cv2.setMouseCallback(windowName, self.click)
            while True:
                frame = self.video.read()
                if frame is None:
                    break

                frame = cv2.flip(src=frame, flipCode=1)
                frame = self.drawDetectingArea(frame, self.points)

                if detecting and len(self.points) > 3:
                    self.model.startDetect(cv2, frame, self.points)

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                elif key == ord("d"):  # close the polygon and start detecting
                    if len(self.points) >= 3:
                        self.points.append(self.points[0])
                        detecting = True
                    print("Need at least 3 points for a valide area.")
                elif key == ord("r"):  # reset polygon and other notifications
                    self.points = []
                    detecting = False
                    self.model.stopDetect()

                cv2.imshow(windowName, frame)

        except KeyboardInterrupt:
            print("Application interrupeted by user.")
        except Exception as e:
            raise e
        finally:
            self.close()


if __name__ == "__main__":
    app = IntrusionDetectionApp(
        [
            "ITDSIU21091@student.hcmiu.edu.vn",
            "ITDSIU21123@student.hcmiu.edu.vn",
            "ITDSIU21117@student.hcmiu.edu.vn",
        ]
    )
    app.run()
