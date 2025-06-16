# Kamera AI Control

This repository contains a minimal example for controlling the **C1 PRO** camera with a controller kit MK2 from a Jetson device. It combines serial commands with a YOLO-based object detection loop.

## Requirements
- Python 3.8+
- `opencv-python`
- `ultralytics`
- `pyserial`

Install dependencies:

```bash
pip install opencv-python ultralytics pyserial
```

## Files
- `camera_controller.py` – basic wrapper for sending serial commands to the camera.
- `ai_camera_control.py` – example that uses a YOLOv8 model to keep a detected person in the center of the frame.

## Usage
1. Connect the controller kit via USB (adjust the serial port if needed).
2. Run the AI controller:

```bash
python ai_camera_control.py --serial /dev/ttyACM0 --video /dev/video0
```

The script loads the small `yolov8n.pt` model by default. When a person is detected, it sends pan/tilt/zoom commands to the camera controller.

