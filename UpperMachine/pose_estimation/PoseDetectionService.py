import time
import yaml
import os

# 动态导入 Estimator
def load_estimator(backend, config):
    if backend == "ov":
        from UpperMachine.pose_estimation.ov.Estimator import HumanPoseEstimator
        model_config = config['models']['ov']
        return HumanPoseEstimator(model_config['model_path'], model_config['device'])
    elif backend == "fastdeploy":
        from UpperMachine.pose_estimation.fastdeploy.Estimator import HumanPoseEstimator
        model_config = config['models']['fastdeploy']
        return HumanPoseEstimator(model_config['model_path'], model_config['device'])
    elif backend == "rdkx5":
        from UpperMachine.pose_estimation.rdkx5.Estimator import HumanPoseEstimator
        model_config = config['models']['rdkx5']
        return HumanPoseEstimator(**model_config)
    else:
        raise ValueError(f"Unsupported backend: {backend}")

from UpperMachine.pose_estimation.posedict2state_vector import posedict2state
from UpperMachine.pose_estimation.state2bytes_vector import state2bytes, state2words
from UpperMachine.pose_estimation.bytes2command import bytes2command, mouse2command
from UpperMachine.pose_estimation.sendcommand import send_command_timeout as send_command
from UpperMachine.pose_estimation.cameras import create_camera

class PoseDetectionService:
    """姿态检测服务"""

    def __init__(self, config_path="Source/flask_config.yml"):
        # 加载配置文件
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        backend = config['pose_backend']
        self.estimator = load_estimator(backend, config)

        # 摄像头配置
        camera_config = config.get('camera', {})
        camera_type = camera_config.get('type', 'rdkx5_imx219')
        camera_kwargs = {
            'width': camera_config.get('width', 640),
            'height': camera_config.get('height', 480),
            'sensor_width': camera_config.get('sensor_width', 1920),
            'sensor_height': camera_config.get('sensor_height', 1080),
            'device_id': camera_config.get('device_id', 0)
        }
        self.camera = create_camera(camera_type, **camera_kwargs)
        try:
            self.camera.open()
        except Exception as e:
            print(f"Warning: Failed to open camera during initialization: {e}")
            self.camera.is_opened = False

        # 配置参数
        self.confidence_threshold = config.get('confidence_threshold', 0.3)
        self.send_commands_enabled = config.get('send_commands_enabled', False)
        self.fps_limit = config.get('fps_limit', 30)
        self.target_ip = config.get('target_ip', '192.168.2.121')

        # 状态变量
        self.is_running = False
        self.current_frame = None
        self.current_poses = None
        self.current_state = None
        self.fps_counter = 0
        self.last_fps_time = time.time()
        self.last_sent_state = None  # 上次发送的姿势状态，避免重复发送相同命令

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
            process_start = time.time()
            print(f"[PROCESS] 开始处理帧")

            # 姿态检测
            infer_start = time.time()
            poses, processed_frame = self.estimator.infer(frame, is_draw=True)
            infer_end = time.time()
            print(f"[PROCESS] 推理时间: {(infer_end - infer_start)*1000:.2f} ms")

            state_name = None
            words_list = []

            if poses is not None and len(poses) > 0:
                # 转换为字典格式
                dict_start = time.time()
                pose_dict = self.estimator.pose2dict(poses)
                dict_end = time.time()
                print(f"[PROCESS] 字典转换时间: {(dict_end - dict_start)*1000:.2f} ms")

                # 转换为状态
                state_start = time.time()
                state_dicts = posedict2state(pose_dict)
                state_end = time.time()
                print(f"[PROCESS] 状态转换时间: {(state_end - state_start)*1000:.2f} ms")
                
                state = [s['index'] for s in state_dicts]  # 仅保留索引
                state_name = [s['name'] for s in state_dicts]  # 仅保留名称
                
                # 计算对应的按键
                words_start = time.time()
                words_list = state2words(state) or []
                words_end = time.time()
                print(f"[PROCESS] 按键计算时间: {(words_end - words_start)*1000:.2f} ms")
                
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
            
            process_end = time.time()
            print(f"[PROCESS] 总处理时间: {(process_end - process_start)*1000:.2f} ms")
            
            return processed_frame, state_name, poses, words_list

            return processed_frame, state_name, poses, words_list

        except Exception as e:
            print(f"帧处理错误: {e}")
            return frame, None, None, None

    def capture_and_process(self):
        """捕获帧并处理"""
        try:
            frame = self.camera.capture()
            return self.process_frame(frame)
        except Exception as e:
            print(f"捕获或处理错误: {e}")
            return None, None, None, None

    def _send_command(self, state):
        """发送控制命令"""
        try:
            # 检查是否与上次发送的状态相同，避免重复发送
            if self.last_sent_state == state:
                return  # 相同状态，不重复发送

            # 转换状态为字节
            keyboard_bytes, mouse_actions = state2bytes(state)

            # 发送键盘命令（如果有键盘操作）
            if keyboard_bytes:
                command = bytes2command(keyboard_bytes)
                result = send_command(server_ip=self.target_ip, command=command, timeout=1.0)

            # 发送鼠标命令
            for mouse_action in mouse_actions:
                command = mouse2command(mouse_action)
                result = send_command(server_ip=self.target_ip, command=command, timeout=1.0)

            # 更新上次发送状态
            self.last_sent_state = state

            # 记录命令历史
            command_info = {
                'command': f"keyboard: {keyboard_bytes}, mouse: {mouse_actions}",
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

    def close(self):
        """关闭服务"""
        if hasattr(self, 'camera') and self.camera:
            self.camera.close()