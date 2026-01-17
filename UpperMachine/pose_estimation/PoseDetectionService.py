import time
import yaml
import os
import threading
import math
import numpy as np

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
from UpperMachine.pose_estimation.bytes2command import bytes2command, mouse2command, combine_mouse_actions
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
        
        # 摄像头视场角类型 (72camera 或 120width_camera)
        self.camera_type_fov = camera_config.get('camera_type', '72camera')
        self.width = camera_kwargs['width']
        self.height = camera_kwargs['height']
        
        print(f"[SERVICE] 当前摄像头 FOV 类型: {self.camera_type_fov}")

        try:
            self.camera.open()
        except Exception as e:
            print(f"Warning: Failed to open camera during initialization: {e}")
            self.camera.is_opened = False

        # 配置参数
        self.confidence_threshold = config.get('confidence_threshold', 0.3)
        self.send_commands_enabled = config.get('send_commands_enabled', False)
        # 检测开关：默认关闭
        self.detection_enabled = config.get('detection_enabled', False)
        self.fps_limit = config.get('fps_limit', 30)
        self.target_ip = config.get('target_ip', '192.168.2.121')
        self.mouse_step_size = config.get('mouse_step_size', 10)
        self.use_async = config.get('use_async', False) # 是否使用异步捕获（串行 vs 异步）

        # 状态变量
        self.is_running = False
        self.frame_buffer = None  # 异步最新帧池
        self.buffer_condition = threading.Condition() # 用于同步捕获与处理
        self.capture_thread = None

        self.current_frame = None
        self.current_poses = None
        self.current_state = None
        self.fps_counter = 0
        self.last_fps_time = time.time()
        self.last_sent_state = None  # 上次发送的姿势状态

        # 采样频率控制：不超过处理频率的3倍，确保数据新鲜
        self.capture_interval = 1.0 / (max(1, self.fps_limit) * 3)

        self.stats = {
            'frames_processed': 0,
            'poses_detected': 0,
            'commands_sent': 0,
            'current_fps': 0
        }

        # 最新原始关键点（用于前端重录）
        self.last_raw_keypoints = None

        # 命令历史
        self.command_history = []

    def _capture_loop(self):
        """独立的摄像头捕获线程 (Producer)"""
        print(f"[CAMERA] 异步捕获线程已启动，最高采样频率: {1.0/self.capture_interval:.1f} Hz")
        while self.is_running:
            loop_start = time.time()
            try:
                if self.camera.is_opened:
                    frame = self.camera.capture()
                    if frame is not None:
                        with self.buffer_condition:
                            self.frame_buffer = frame # 始终覆盖，池子只保留最新一张
                            self.buffer_condition.notify_all() # 通知处理线程
                else:
                    time.sleep(0.5)
            except Exception as e:
                if "Failed to capture" not in str(e):
                    print(f"[CAMERA] 捕获错误: {e}")
                time.sleep(0.1)
            
            # 限制采样频率
            elapsed = time.time() - loop_start
            if elapsed < self.capture_interval:
                time.sleep(self.capture_interval - elapsed)

    def start(self):
        """启动后台服务"""
        if not self.is_running:
            self.is_running = True
            if self.use_async:
                # 仅在异步模式下启动独立的捕获线程
                self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
                self.capture_thread.start()
            else:
                print("[SERVICE] 当前处于串行模式 (Serial Mode)")

    def capture_and_process(self):
        """获取最新一帧并处理 (支持异步池或串行捕获)"""
        try:
            frame = None
            
            if self.use_async:
                # 异步模式：从池子中取最新帧
                with self.buffer_condition:
                    # 如果没有新帧，则等待（满足“模型等待摄像头”的需求）
                    while self.frame_buffer is None and self.is_running:
                        if not self.buffer_condition.wait(timeout=1.0):
                            return None, None, None, None
                    
                    if self.frame_buffer is not None:
                        frame = self.frame_buffer.copy()
                        self.frame_buffer = None # 取走后清空，确保下一波是新鲜的
            else:
                # 串行模式：直接实时捕获
                if self.camera.is_opened:
                    frame = self.camera.capture()
            
            if frame is None:
                return None, None, None, None
                
            return self.process_frame(frame)
        except Exception as e:
            print(f"[PROCESS] 处理错误: {e}")
            return None, None, None, None

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
                
                # 处理镜像产生的左右互换逻辑
                # 虽然显示画面为了直观进行了翻转，但模型是在原始镜像画面上进行推理的
                # 这会导致物理右手被识别为 left_wrist。在此进行逻辑层面的交换。
                swap_list = [
                    ('left_eye', 'right_eye'), ('left_ear', 'right_ear'),
                    ('left_shoulder', 'right_shoulder'), ('left_elbow', 'right_elbow'),
                    ('left_wrist', 'right_wrist'), ('left_hip', 'right_hip'),
                    ('left_knee', 'right_knee'), ('left_ankle', 'right_ankle')
                ]
                for left_key, right_key in swap_list:
                    if left_key in pose_dict and right_key in pose_dict:
                        # 交换坐标值
                        pose_dict[left_key], pose_dict[right_key] = pose_dict[right_key], pose_dict[left_key]
                
                # 更新全局最新的原始关键点记录 (针对交换后的正确逻辑)
                serialized_keypoints = {k: [float(x) for x in v] for k, v in pose_dict.items()}
                self.last_raw_keypoints = serialized_keypoints

                dict_end = time.time()
                print(f"[PROCESS] 字典转换时间: {(dict_end - dict_start)*1000:.2f} ms")

                # 转换为状态
                state_start = time.time()
                state_dicts = posedict2state(pose_dict, current_camera=self.camera_type_fov)
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

        except Exception as e:
            print(f"帧处理错误: {e}")
            return frame, None, None, None

    def _send_command(self, state):
        """发送控制命令"""
        try:
            # 1. 转换状态为字节和动作
            keyboard_bytes, mouse_actions = state2bytes(state)

            # 2. 识别是否包含瞬时动作（位移或滚轮）
            # -7, -8: 滚轮; -9, -10: 左右移动
            has_transient_mouse = any(a in [-7, -8, -9, -10] for a in mouse_actions)

            # 3. 基础过滤：如果状态未变且没有瞬时动作，由于 HID 指令具有持久化特性，无需重复发送
            if self.last_sent_state == state and not has_transient_mouse:
                return

            # 4. 处理键盘指令：仅在键盘按键列表变化时发送
            current_kb = sorted(keyboard_bytes)
            last_kb = sorted(getattr(self, 'last_kb_sent', []))
            if current_kb != last_kb:
                command = bytes2command(keyboard_bytes)
                send_command(server_ip=self.target_ip, command=command, timeout=1.0)
                self.last_kb_sent = keyboard_bytes

            # 5. 处理鼠标指令：将所有鼠标动作合并为一个报文发送
            # 如果包含移动动作，需要强制发送（ignore_cache=True）以实现连续移动效果
            mouse_command = combine_mouse_actions(mouse_actions, step_size=self.mouse_step_size)
            result = send_command(
                server_ip=self.target_ip, 
                command=mouse_command, 
                timeout=1.0,
                ignore_cache=has_transient_mouse
            )

            # 更新状态记录
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

    def send_stop_command(self):
        """发送停止命令（全0键盘命令）以停止HID输出"""
        try:
            # 发送全0键盘命令
            command = bytes2command([])  # 空列表会生成全0命令
            result = send_command(server_ip=self.target_ip, command=command, timeout=1.0)
            
            # 记录命令历史
            command_info = {
                'command': 'stop_command: keyboard all zeros',
                'result': result,
                'timestamp': time.time(),
                'state': 'stop'
            }

            self.command_history.append(command_info)
            if len(self.command_history) > 100:
                self.command_history.pop(0)

            print("[SERVICE] 已发送停止命令")
            return command_info

        except Exception as e:
            print(f"停止命令发送错误: {e}")
            return None

    def stop(self):
        """停止检测并发送停止命令"""
        # 停止循环但不关闭摄像头，以便可以快速恢复
        self.is_running = False
        try:
            self.send_stop_command()
        except Exception as e:
            print(f"停止检测时发送停止命令失败: {e}")

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
        stats = self.stats.copy()
        stats['is_running'] = self.is_running
        return stats

    def close(self):
        """关闭服务"""
        if hasattr(self, 'camera') and self.camera:
            self.camera.close()