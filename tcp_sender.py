# 本文件用于获取车载摄像头的信息
import socket
import time

import cv2
import numpy as np

# 使用ESP32Cam作为服务器，端口为80，服务器只会接收一次，然后就断开，不会保持连接，所以每次都需要创建一个socket
def send_command(server_ip='192.168.2.184', port=80):
    # 创建一个TCP/IP套接字
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 连接到服务器
        sock.connect((server_ip, port))

        http_request = "GET"
        sock.sendall(http_request.encode())

    finally:
        # 关闭套接字
        sock.close()

if __name__ == "__main__":
    # 从ESP32-CAM获取图像
    img = send_command(server_ip='192.168.2.184')  # 替换为您的ESP32-CAM IP地址