"""Simple AI-based PTZ control for the C1 PRO camera."""

import argparse
import time
from typing import Optional

import cv2
from ultralytics import YOLO

from camera_controller import CameraController


class AIFollower:
    def __init__(self, controller: CameraController, model: Optional[str] = None, device: str = "cpu"):
        self.controller = controller
        # Use a tiny YOLOv8 model by default
        self.model = YOLO(model or "yolov8n.pt")
        self.model.fuse()
        self.device = device

    def run(self, video_source: str = "/dev/video0", conf: float = 0.3) -> None:
        cap = cv2.VideoCapture(video_source)
        if not cap.isOpened():
            print("Could not open video source")
            return

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        center_x = frame_width // 2
        center_y = frame_height // 2

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            results = self.model.predict(frame, device=self.device, verbose=False)[0]
            boxes = results.boxes
            person = None
            for box in boxes:
                if int(box.cls[0]) == 0:  # class 0 -> person
                    person = box
                    break
            if person is not None:
                x1, y1, x2, y2 = person.xyxy[0].cpu().tolist()
                obj_center_x = int((x1 + x2) / 2)
                obj_center_y = int((y1 + y2) / 2)
                dx = obj_center_x - center_x
                dy = obj_center_y - center_y
                # Simple proportional control for pan/tilt
                pan_val = int(dx * 0.1)
                tilt_val = int(dy * 0.1)
                if abs(pan_val) > 1:
                    self.controller.pan(pan_val)
                if abs(tilt_val) > 1:
                    self.controller.tilt(tilt_val)
                # Zoom based on bbox size
                bbox_width = x2 - x1
                zoom_value = int(10000 + (frame_width - bbox_width) * 5)
                self.controller.set_zoom(zoom_value)
            # Small delay
            if cv2.waitKey(1) == 27:
                break
            time.sleep(0.05)

        cap.release()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI PTZ controller")
    parser.add_argument("--video", default="/dev/video0", help="Video source (file or device)")
    parser.add_argument("--model", default="yolov8n.pt", help="Path to YOLO model")
    parser.add_argument("--serial", default="/dev/ttyACM0", help="Camera controller serial port")
    args = parser.parse_args()

    controller = CameraController(port=args.serial)
    follower = AIFollower(controller, model=args.model)
    controller.wake_up()
    controller.set_mode_day()

    follower.run(video_source=args.video)

