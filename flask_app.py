"""
基于Flask和Socket.IO的实时摄像头姿态检测应用
提供更灵活的自定义功能和更好的性能控制
"""

from flask import Flask, render_template, Response, jsonify, request
from flask_socketio import SocketIO, emit
import cv2
import base64
import json
import threading
import time
from queue import Queue
import numpy as np

# 导入姿态检测相关模块
from UpperMachine.fastdeploy.Estimator import HumanPoseEstimator
from UpperMachine.fastdeploy.utils import draw_poses, body_mapper
from UpperMachine.posedict2state_vector import posedict2state
from UpperMachine.state2bytes_vector import state2bytes
from UpperMachine.bytes2command import bytes2command
from UpperMachine.sendcommand import send_command_timeout as send_command

app = Flask(__name__, template_folder='GUI/flask/templates')
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

class PoseDetectionService:
    """姿态检测服务"""
    
    def __init__(self):
        self.model_path = "Source/Models/tinypose_128x96"
        self.device = "CPU"
        self.estimator = HumanPoseEstimator(self.model_path, self.device)
        
        # 配置参数
        self.confidence_threshold = 0.3
        self.send_commands_enabled = False
        self.fps_limit = 30
        
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
            state_bytes = state2bytes(state)
            
            # 转换为命令
            command = bytes2command(state_bytes)
            
            # 发送命令
            result = send_command(command, timeout=1.0)
            
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

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    """配置API"""
    if request.method == 'POST':
        data = request.get_json()
        
        if 'confidence_threshold' in data:
            pose_service.confidence_threshold = float(data['confidence_threshold'])
        
        if 'send_commands_enabled' in data:
            pose_service.send_commands_enabled = bool(data['send_commands_enabled'])
        
        if 'fps_limit' in data:
            pose_service.fps_limit = int(data['fps_limit'])
        
        return jsonify({'status': 'success'})
    
    else:
        return jsonify({
            'confidence_threshold': pose_service.confidence_threshold,
            'send_commands_enabled': pose_service.send_commands_enabled,
            'fps_limit': pose_service.fps_limit
        })

@app.route('/api/stats')
def stats():
    """统计信息API"""
    return jsonify(pose_service.get_stats())

@app.route('/api/commands')
def commands():
    """命令历史API"""
    count = request.args.get('count', 10, type=int)
    return jsonify(pose_service.get_recent_commands(count))

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print('客户端已连接')
    emit('status', {'message': '连接成功'})

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接"""
    print('客户端已断开连接')

@socketio.on('start_camera')
def handle_start_camera():
    """启动摄像头"""
    if not pose_service.is_running:
        pose_service.is_running = True
        threading.Thread(target=camera_thread, daemon=True).start()
        emit('status', {'message': '摄像头已启动'})

@socketio.on('stop_camera')
def handle_stop_camera():
    """停止摄像头"""
    pose_service.is_running = False
    emit('status', {'message': '摄像头已停止'})

@socketio.on('update_config')
def handle_update_config(data):
    """更新配置"""
    try:
        if 'confidence_threshold' in data:
            pose_service.confidence_threshold = float(data['confidence_threshold'])
        
        if 'send_commands_enabled' in data:
            pose_service.send_commands_enabled = bool(data['send_commands_enabled'])
        
        if 'fps_limit' in data:
            pose_service.fps_limit = int(data['fps_limit'])
        
        emit('config_updated', {
            'confidence_threshold': pose_service.confidence_threshold,
            'send_commands_enabled': pose_service.send_commands_enabled,
            'fps_limit': pose_service.fps_limit
        })
        
    except Exception as e:
        emit('error', {'message': f'配置更新失败: {e}'})

def camera_thread():
    """摄像头处理线程"""
    cap = cv2.VideoCapture(0)
    
    # 检查摄像头是否成功打开
    if not cap.isOpened():
        socketio.emit('error', {'message': '无法打开摄像头'})
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, pose_service.fps_limit)
    
    frame_time = 1.0 / pose_service.fps_limit
    
    try:
        while pose_service.is_running:
            start_time = time.time()
            
            ret, frame = cap.read()
            if not ret:
                print("无法读取摄像头画面")
                break
            
            # 处理帧
            processed_frame, state, poses = pose_service.process_frame(frame)
            
            # 安全检查processed_frame
            if processed_frame is None:
                processed_frame = frame
            
            # 编码图像为base64
            try:
                _, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
            except Exception as e:
                print(f"图像编码错误: {e}")
                continue
            
            # 安全计算poses数量
            poses_count = 0
            if poses is not None:
                try:
                    poses_count = len(poses)
                except:
                    poses_count = poses.shape[0] if hasattr(poses, 'shape') else 0
            
            # 发送数据到客户端
            try:
                socketio.emit('frame_update', {
                    'image': frame_base64,
                    'state': state,
                    'poses_count': poses_count,
                    'stats': pose_service.get_stats()
                })
            except Exception as e:
                print(f"数据发送错误: {e}")
            
            # 控制帧率
            elapsed = time.time() - start_time
            if elapsed < frame_time:
                time.sleep(frame_time - elapsed)
    
    except Exception as e:
        print(f"摄像头线程错误: {e}")
        socketio.emit('error', {'message': f'摄像头错误: {e}'})
    
    finally:
        cap.release()
        pose_service.is_running = False
        socketio.emit('status', {'message': '摄像头已关闭'})

if __name__ == '__main__':
    # 创建模板目录
    import os
    os.makedirs('templates', exist_ok=True)
    
    # 运行应用
    print("启动Flask应用...")
    print("访问 http://localhost:5000 查看实时姿态检测")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)