import sys
import cv2
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QHBoxLayout
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtCore import QTimer, Qt

# 假设的图像处理函数，返回一个整数 N
def process_frame(frame):
    # 这里可以加入图像处理逻辑，目前仅返回固定值 N
    return 42  # 示例返回值

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
            # 将OpenCV图像转换为Qt格式
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.camera_label.setPixmap(QPixmap.fromImage(qt_image))

            # 处理图像并更新右侧标签
            result_value = process_frame(frame)
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