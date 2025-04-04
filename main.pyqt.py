import sys
import cv2
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QHBoxLayout
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtCore import QTimer, Qt

from Tools.bytes2command import bytes2command
from Tools.sendcommand import send_commands_timeout as send_command
# from Tools.state2bytes import state2bytes
from Tools.posedict2state_vector import posedict2state
from Tools.state2bytes_vector import state2bytes

# from Tools.ov.Estimator import HumanPoseEstimator
# model_path = "Models/human-pose-estimation-0001/FP16-INT8/human-pose-estimation-0001.xml"
# device = "CPU"
# estimator = HumanPoseEstimator(model_path, device)

IF_SEND_COMMAND = True # 是否发送命令
DEBUG_FLAG = "undebug" # 调试模式，可选值："debug"、"undebug"

from Tools.fastdeploy.Estimator import HumanPoseEstimator
model_path = "Models/tinypose_128x96"
device = "CPU"
estimator = HumanPoseEstimator(model_path, device)

server_ip = '192.168.2.184'
port = 80

# 假设的图像处理函数，返回一个整数 N
def process_frame(poses):
    if len(poses) == 0:
        return ""
    gesture_list = posedict2state(poses, type=DEBUG_FLAG)
    bytes_list = state2bytes(gesture_list)
    command = bytes2command(bytes_list)
    if IF_SEND_COMMAND:
        send_command(server_ip=server_ip, port=port, command=command)
    return "/".join([str(x) for x in gesture_list])  # 示例返回值

class CameraApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Camera App")
        # self.setGeometry(100, 100, 800, 400)

        # 主窗口部件和布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)

        # 左侧：摄像头画面
        self.camera_label = QLabel()
        self.layout.addWidget(self.camera_label)

        # 右侧：显示处理结果的标签
        self.result_label = QLabel()
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setWordWrap(True)  # 启用自动换行
        self.result_label.setFixedWidth(800)  # 设置固定宽度为800
        font = QFont() # 设置字体大小
        font.setPointSize(50)  # 将字体大小设置为20点
        self.result_label.setFont(font)
        self.layout.addWidget(self.result_label)

        # 初始化摄像头
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open camera.")
            sys.exit()

        # 定时器用于以30fps更新画面
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(int(1000 / 30))  # 约30fps

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            # 反转图像以保持镜像
            frame = cv2.flip(frame, 1)  # 水平翻转
            # 调用推理函数进行推理
            poses, drawed_frame = estimator.infer(frame, True)

            # 将OpenCV图像转换为Qt格式
            rgb_image = cv2.cvtColor(drawed_frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)

            self.camera_label.setPixmap(QPixmap.fromImage(qt_image))

            # 处理图像并更新右侧标签
            pose_dict = estimator.pose2dict(poses)
            result_value = process_frame(pose_dict)
            self.result_label.setText(f"{result_value}")

    def closeEvent(self, event):
        # 释放摄像头资源
        self.cap.release()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = CameraApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()