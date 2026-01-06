from abc import ABC, abstractmethod
import cv2
import numpy as np

class Camera(ABC):
    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height
        self.is_opened = False

    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def capture(self):
        """Capture an image and return as BGR numpy array"""
        pass

    @abstractmethod
    def close(self):
        pass

    def resize_image(self, img, width=None, height=None):
        if width is None:
            width = self.width
        if height is None:
            height = self.height
        return cv2.resize(img, (width, height))

from .rdkx5_IMX219 import Rdkx5Imx219Camera
from .usb_camera import UsbCamera

def create_camera(camera_type, **kwargs):
    if camera_type == 'rdkx5_imx219':
        # Filter kwargs for Rdkx5Imx219Camera
        valid_kwargs = {k: v for k, v in kwargs.items() if k in ['width', 'height', 'sensor_width', 'sensor_height']}
        return Rdkx5Imx219Camera(**valid_kwargs)
    elif camera_type == 'usb':
        # Filter kwargs for UsbCamera
        valid_kwargs = {k: v for k, v in kwargs.items() if k in ['width', 'height', 'device_id']}
        return UsbCamera(**valid_kwargs)
    else:
        raise ValueError(f"Unknown camera type: {camera_type}")