from flask import render_template, jsonify, request
from flask_socketio import emit
import cv2
import base64
import json
import threading
import time
from queue import Queue
import numpy as np

from UpperMachine.pose_estimation.PoseDetectionService import PoseDetectionService

# 创建服务实例
pose_service = PoseDetectionService()

def register_routes(app, socketio):
    @app.route('/')
    def index():
        """主页面"""
        return render_template('index.html')

    @app.route('/realtime')
    def realtime():
        """实时检测页面"""
        return render_template('realtime.html')

    @app.route('/debug')
    def debug():
        """调试工具页面"""
        return render_template('debug.html')

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
            
            if 'target_ip' in data:
                pose_service.target_ip = str(data['target_ip'])
            
            return jsonify({'status': 'success'})
        
        else:
            return jsonify({
                'confidence_threshold': pose_service.confidence_threshold,
                'send_commands_enabled': pose_service.send_commands_enabled,
                'fps_limit': pose_service.fps_limit,
                'target_ip': pose_service.target_ip
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
            
            if 'target_ip' in data:
                pose_service.target_ip = str(data['target_ip'])
            
            emit('config_updated', {
                'confidence_threshold': pose_service.confidence_threshold,
                'send_commands_enabled': pose_service.send_commands_enabled,
                'fps_limit': pose_service.fps_limit,
                'target_ip': pose_service.target_ip
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
                
                # 水平翻转画面（镜像）
                frame = cv2.flip(frame, 1)
                
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

    # 调试工具路由
    @app.route('/api/send_mouse', methods=['POST'])
    def send_mouse():
        data = request.json
        url = data.get('url', '192.168.2.121')
        port = data.get('port', 80)
        words = data.get('words', 'a')
        
        try:
            from UpperMachine.pose_estimation.sendcommand import send_command_timeout as send_command
            from UpperMachine.pose_estimation.bytes2command import bytes2command
            from UpperMachine.pose_estimation.state2bytes_vector import words2bytes
            
            result = send_command(url, port, bytes2command(words2bytes(words)))
            return jsonify({'status': 'success', 'result': str(result)})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})

    @app.route('/api/detect_pose', methods=['POST'])
    def detect_pose():
        if 'image' not in request.files:
            return jsonify({'status': 'error', 'message': 'No image provided'})
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No image selected'})
        
        try:
            # 读取图像
            img_array = np.frombuffer(file.read(), np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            # 检测姿态
            poses, processed_img = pose_service.estimator.infer(img, True)
            
            # 编码为base64
            _, buffer = cv2.imencode('.jpg', processed_img)
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            
            return jsonify({'status': 'success', 'image': img_base64, 'poses': poses.tolist() if poses is not None else []})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})

    @app.route('/api/save_pose', methods=['POST'])
    def save_pose():
        data = request.json
        # 实现保存逻辑，类似debug.gradio.py的fn_btn_save
        # 这里需要img_raw，但前端需要发送base64或重新上传
        # 简化版
        return jsonify({'status': 'success'})