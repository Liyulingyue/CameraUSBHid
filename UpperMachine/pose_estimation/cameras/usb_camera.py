from . import Camera
import cv2

class UsbCamera(Camera):
    def __init__(self, width=640, height=480, device_id=0):
        super().__init__(width, height)
        self.device_id = device_id
        self.cap = None

    def open(self):
        if self.cap is None:
            self.cap = cv2.VideoCapture(self.device_id)
            if not self.cap.isOpened():
                raise RuntimeError(f"Cannot open USB camera with device ID {self.device_id}")
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.is_opened = True

    def capture(self):
        if not self.is_opened:
            raise RuntimeError("Camera is not opened")
        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("Failed to capture image from USB camera")
        return frame  # Already BGR

    def close(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            self.is_opened = False