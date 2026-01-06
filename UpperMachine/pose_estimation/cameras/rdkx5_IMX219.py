from . import Camera
import numpy as np
import cv2

# Camera API libs
try:
    from hobot_vio import libsrcampy as srcampy
except ImportError:
    from hobot_vio_rdkx5 import libsrcampy as srcampy

class Rdkx5Imx219Camera(Camera):
    def __init__(self, width=640, height=480, sensor_width=1920, sensor_height=1080):
        super().__init__(width, height)
        self.sensor_width = sensor_width
        self.sensor_height = sensor_height
        self.cam = None

    def open(self):
        if self.cam is None:
            self.cam = srcampy.Camera()
            self.cam.open_cam(0, -1, -1, [self.sensor_width, self.sensor_width], [self.sensor_height, self.sensor_height], self.sensor_height, self.sensor_width)
            self.is_opened = True

    def capture(self):
        if not self.is_opened:
            raise RuntimeError("Camera is not opened")
        img_buffer = self.cam.get_img(2, self.sensor_width, self.sensor_height)
        if img_buffer is None:
            raise RuntimeError("Failed to capture image from camera")
        img_np = np.frombuffer(img_buffer, dtype=np.uint8)
        img_nv12 = img_np.reshape((int(self.sensor_height * 1.5), self.sensor_width))
        img_bgr = cv2.cvtColor(img_nv12, cv2.COLOR_YUV2BGR_NV12)
        return self.resize_image(img_bgr)

    def close(self):
        if self.cam is not None:
            self.cam.close_cam()
            self.cam = None
            self.is_opened = False