import serial
import time
import logging
from typing import Optional


class CameraController:
    """Simple controller wrapper for the C1 PRO camera with controller kit MK2."""

    def __init__(self, port: str = "/dev/ttyACM0", baudrate: int = 115200, timeout: float = 1) -> None:
        self.port = port
        self.baudrate = baudrate
        try:
            self.serial = serial.Serial(port, baudrate, timeout=timeout)
            # Wait for controller to be ready
            time.sleep(2)
            self._log("Serial connection established.")
        except Exception as exc:
            self.serial = None
            self._log(f"Failed to open serial port: {exc}", error=True)

    def _log(self, message: str, error: bool = False) -> None:
        prefix = "[CameraController]"
        if error:
            logging.error(f"{prefix} {message}")
        else:
            logging.info(f"{prefix} {message}")
        print(f"{prefix} {message}")

    def send_command(self, cmd: str) -> Optional[str]:
        """Send raw command to the controller and return its response."""
        if not self.serial or not self.serial.is_open:
            self._log("Serial port not open", error=True)
            return None
        full_cmd = (cmd.strip() + "\r\n").encode("utf-8")
        self.serial.write(full_cmd)
        self._log(f">>> {cmd}")
        time.sleep(0.05)
        response = self.serial.read_all().decode("utf-8", errors="ignore")
        self._log(f"<<< {response.strip()}")
        return response.strip()

    # ---------------------------------------------------------------
    # Basic operations
    # ---------------------------------------------------------------
    def wake_up(self) -> None:
        self.send_command("M238")
        self.send_command("M8")
        self.send_command("version")
        self.ir_off()

    def autofocus(self) -> None:
        self.send_command("G91")
        self.send_command("M246")
        self.send_command("M240 A50")
        self.send_command("G0 A30000")
        self.send_command("M0 A")

    def set_zoom(self, value: int) -> None:
        self.send_command(f"G0 A{value}")
        self.send_command("M0 A")

    def set_focus(self, value: int) -> None:
        self.send_command(f"G0 B{value}")
        self.send_command("M0 B")

    def ir_on(self) -> None:
        self.send_command("M242 A1")

    def ir_off(self) -> None:
        self.send_command("M242 A0")

    def set_mode_day(self) -> None:
        self.send_command("M241 A0")
        self.send_command("M240 A50")
        self.send_command("M250 A10")
        self.ir_off()

    def set_mode_night(self) -> None:
        self.send_command("M241 A0")
        self.send_command("M240 A5")
        self.send_command("M250 A40")
        self.ir_on()

    # ---------------------------------------------------------------
    # PTZ examples (customize according to your controller's protocol)
    # ---------------------------------------------------------------
    def pan(self, value: int) -> None:
        """Pan to absolute position (example command)."""
        self.send_command(f"G0 X{value}")
        self.send_command("M0 X")

    def tilt(self, value: int) -> None:
        """Tilt to absolute position (example command)."""
        self.send_command(f"G0 Y{value}")
        self.send_command("M0 Y")

    def autofocus_loop(
        self,
        video_device: str = "/dev/video0",
        min_focus: int = 0,
        max_focus: int = 60000,
        step: int = 2000,
    ) -> None:
        import cv2
        cap = cv2.VideoCapture(video_device)
        if not cap.isOpened():
            self._log("Could not open video device", error=True)
            return

        best_focus = min_focus
        best_value = -1.0
        self._log("Running Laplacian autofocus sweep...")
        for focus in range(min_focus, max_focus + 1, step):
            self.set_focus(focus)
            time.sleep(0.15)
            ret, frame = cap.read()
            if not ret:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            lap = cv2.Laplacian(gray, cv2.CV_64F)
            value = lap.var()
            self._log(f"Focus {focus} → variance {value:.2f}")
            if value > best_value:
                best_value = value
                best_focus = focus
        self._log(f"Best focus {best_focus} (var {best_value:.2f})")
        self.set_focus(best_focus)
        cap.release()

