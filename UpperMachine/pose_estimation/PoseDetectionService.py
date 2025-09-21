import time

from UpperMachine.pose_estimation.ov.Estimator import HumanPoseEstimator
from UpperMachine.pose_estimation.posedict2state_vector import posedict2state
from UpperMachine.pose_estimation.state2bytes_vector import state2bytes
from UpperMachine.pose_estimation.bytes2command import bytes2command
from UpperMachine.pose_estimation.sendcommand import send_command_timeout as send_command

class PoseDetectionService:
    """姿态检测服务"""

    def __init__(self):
        self.model_path = "Source/Models/human-pose-estimation-0001/FP32/human-pose-estimation-0001.xml"
        self.device = "CPU"
        self.estimator = HumanPoseEstimator(self.model_path, self.device)

        # 配置参数
        self.confidence_threshold = 0.3
        self.send_commands_enabled = False
        self.fps_limit = 30
        self.target_ip = '192.168.2.121'  # 目标设备IP地址

        # 状态变量
        self.is_running = False
        self.current_frame = None
        self.current_poses = None
        self.current_state = None
        self.fps_counter = 0
        self.last_fps_time = time.time()

        # 统计信息
        self.stats = {
            'frames_processed': 0,
            'poses_detected': 0,
            'commands_sent': 0,
            'current_fps': 0
        }

        # 命令历史
        self.command_history = []

    def process_frame(self, frame):
        """处理单帧图像"""
        try:
            start_time = time.time()

            # 姿态检测
            poses, processed_frame = self.estimator.infer(frame, is_draw=True)

            state = None

            if poses is not None and len(poses) > 0:
                # 转换为字典格式
                pose_dict = self.estimator.pose2dict(poses)

                # 转换为状态
                state = posedict2state(pose_dict)
                self.current_state = state
                self.current_poses = pose_dict

                # 发送命令
                if self.send_commands_enabled:
                    self._send_command(state)

                self.stats['poses_detected'] += 1

            self.stats['frames_processed'] += 1
            self.current_frame = processed_frame

            # 计算FPS
            self._update_fps()

            return processed_frame, state, poses

        except Exception as e:
            print(f"帧处理错误: {e}")
            return frame, None, None

    def _send_command(self, state):
        """发送控制命令"""
        try:
            # 转换状态为字节
            keyboard_bytes, mouse_actions = state2bytes(state)
            state_bytes = keyboard_bytes
            # TODO: 补充鼠标动作的处理
            # 转换为命令
            command = bytes2command(state_bytes)

            # 发送命令
            result = send_command(server_ip=self.target_ip, command=command, timeout=1.0)

            # 记录命令历史
            command_info = {
                'command': command.hex(),
                'result': result,
                'timestamp': time.time(),
                'state': state
            }

            self.command_history.append(command_info)
            if len(self.command_history) > 100:  # 保持最近100条记录
                self.command_history.pop(0)

            self.stats['commands_sent'] += 1

            return command_info

        except Exception as e:
            print(f"命令发送错误: {e}")
            return None

    def _update_fps(self):
        """更新FPS计算"""
        self.fps_counter += 1
        current_time = time.time()

        if current_time - self.last_fps_time >= 1.0:
            self.stats['current_fps'] = self.fps_counter
            self.fps_counter = 0
            self.last_fps_time = current_time

    def get_stats(self):
        """获取统计信息"""
        return self.stats.copy()

    def get_recent_commands(self, count=10):
        """获取最近的命令历史"""
        return self.command_history[-count:] if self.command_history else []

# 全局服务实例
pose_service = PoseDetectionService()