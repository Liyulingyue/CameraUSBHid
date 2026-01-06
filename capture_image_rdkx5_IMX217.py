#!/usr/bin/env python3

import sys
import time
import argparse
import numpy as np
import cv2
from UpperMachine.pose_estimation.cameras import create_camera

def main():
    parser = argparse.ArgumentParser(description='Capture images from camera')
    parser.add_argument('--width', type=int, default=640, help='Output image width')
    parser.add_argument('--height', type=int, default=480, help='Output image height')
    parser.add_argument('--camera_type', type=str, default='rdkx5_imx219', choices=['rdkx5_imx219', 'usb'], help='Camera type')
    parser.add_argument('--device_id', type=int, default=0, help='Device ID for USB camera')
    args = parser.parse_args()

    # Create camera
    camera = create_camera(args.camera_type, width=args.width, height=args.height, device_id=args.device_id)

    # Open camera
    camera.open()

    times = []
    for i in range(1, 11):
        start_time = time.time()
        img_bgr = camera.capture()
        filename = f'captured_image{i}.jpg'
        cv2.imwrite(filename, img_bgr)
        end_time = time.time()
        capture_time = end_time - start_time
        times.append(capture_time)
        print(f"Image {i} saved as {filename}, size: {args.width} x {args.height}, time: {capture_time:.2f} seconds")

    # Close camera
    camera.close()

    average_time = sum(times) / len(times)
    print(f"Average capture time for 10 images: {average_time:.2f} seconds")

if __name__ == '__main__':
    main()