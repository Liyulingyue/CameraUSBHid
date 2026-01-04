#!/usr/bin/env python3
"""
树莓派摄像头测试脚本
测试摄像头读取性能和正确性
支持 CSI 摄像头 (picamera) 和 USB 摄像头 (OpenCV)
"""

import time
import sys
import numpy as np

# 尝试导入 picamera (用于 CSI 摄像头)
try:
    from picamera import PiCamera
    from picamera.array import PiRGBArray
    PICAMERA_AVAILABLE = True
except ImportError:
    PICAMERA_AVAILABLE = False
    print("picamera 未安装，将使用 OpenCV")

# OpenCV
import cv2

def test_raspberry_pi_camera(width=640, height=480, fps=30, test_frames=50):
    """
    使用 picamera 测试树莓派 CSI 摄像头
    """
    if not PICAMERA_AVAILABLE:
        print("❌ picamera 未安装")
        print("安装: pip install picamera")
        return False

    print("使用树莓派 CSI 摄像头 (picamera)")
    print(f"分辨率: {width}x{height}, FPS: {fps}")
    print(f"测试帧数: {test_frames}")
    print("-" * 50)

    try:
        camera = PiCamera()
        camera.resolution = (width, height)
        camera.framerate = fps

        raw_capture = PiRGBArray(camera, size=(width, height))

        # 预热摄像头
        time.sleep(2)

        frame_times = []
        start_time = time.time()

        for i, frame in enumerate(camera.capture_continuous(raw_capture, format="bgr", use_video_port=True)):
            if i >= test_frames:
                break

            frame_start = time.time()

            # 获取图像
            image = frame.array

            frame_time = time.time() - frame_start
            frame_times.append(frame_time)

            if i < 5:
                print(".2f")

            # 显示图像
            cv2.imshow('Raspberry Pi Camera Test', image)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # 清空缓冲区
            raw_capture.truncate(0)

        # 统计
        total_time = time.time() - start_time
        avg_frame_time = sum(frame_times) / len(frame_times) if frame_times else 0
        actual_fps = len(frame_times) / total_time if total_time > 0 else 0

        print("-" * 50)
        print("CSI 摄像头测试结果:")
        print(".2f")
        print(".2f")
        print(".2f")

        if avg_frame_time < 0.033:
            print("✅ CSI 摄像头性能良好")
        else:
            print("⚠️ CSI 摄像头性能一般")

        camera.close()
        cv2.destroyAllWindows()
        return True

    except Exception as e:
        print(f"❌ CSI 摄像头测试失败: {e}")
        return False

def test_usb_camera(device=0, width=640, height=480, fps=30, test_frames=50):
    """
    使用 OpenCV 测试 USB 摄像头
    """
    print(f"测试 USB 摄像头设备 {device}")
    print(f"分辨率: {width}x{height}, 目标 FPS: {fps}")
    print(f"测试帧数: {test_frames}")
    print("-" * 50)

    cap = cv2.VideoCapture(device)

    if not cap.isOpened():
        print(f"❌ 无法打开 USB 摄像头设备 {device}")
        print("可能的原因:")
        print("1. 摄像头未连接")
        print("2. 设备索引错误")
        print("3. 权限问题")
        return False

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, fps)

    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = cap.get(cv2.CAP_PROP_FPS)

    print(f"实际分辨率: {actual_width}x{actual_height}")
    print(f"实际 FPS: {actual_fps}")
    print("-" * 50)

    frame_times = []
    start_time = time.time()

    for i in range(test_frames):
        frame_start = time.time()

        ret, frame = cap.read()
        if not ret:
            print(f"❌ 第 {i+1} 帧读取失败")
            break

        frame_time = time.time() - frame_start
        frame_times.append(frame_time)

        if i < 5:
            print(".2f")

        cv2.imshow('USB Camera Test', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    total_time = time.time() - start_time
    avg_frame_time = sum(frame_times) / len(frame_times) if frame_times else 0
    actual_fps_measured = len(frame_times) / total_time if total_time > 0 else 0

    print("-" * 50)
    print("USB 摄像头测试结果:")
    print(".2f")
    print(".2f")
    print(".2f")

    if avg_frame_time < 0.033:
        print("✅ USB 摄像头性能良好")
    else:
        print("⚠️ USB 摄像头性能一般")

    cap.release()
    cv2.destroyAllWindows()
    return True

if __name__ == "__main__":
    camera_type = sys.argv[1] if len(sys.argv) > 1 else "auto"
    device = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 640
    height = int(sys.argv[4]) if len(sys.argv) > 4 else 480
    fps = int(sys.argv[5]) if len(sys.argv) > 5 else 30
    test_frames = int(sys.argv[6]) if len(sys.argv) > 6 else 30

    try:
        if camera_type == "csi" or (camera_type == "auto" and PICAMERA_AVAILABLE):
            print("尝试使用 CSI 摄像头...")
            success = test_raspberry_pi_camera(width, height, fps, test_frames)
            if not success and camera_type == "auto":
                print("CSI 摄像头失败，尝试 USB 摄像头...")
                test_usb_camera(device, width, height, fps, test_frames)
        else:
            test_usb_camera(device, width, height, fps, test_frames)
    except KeyboardInterrupt:
        print("\n测试中断")
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"测试出错: {e}")
        cv2.destroyAllWindows()