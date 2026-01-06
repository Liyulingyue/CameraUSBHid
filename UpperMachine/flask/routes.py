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
from UpperMachine.utils import convert_numpy_to_list

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

    @app.route('/mouse_control')
    def mouse_control():
        """鼠标远程控制页面"""
        return render_template('mouse_control.html')

    @app.route('/pose_recorder')
    def pose_recorder():
        """姿势录制与配置页面"""
        return render_template('pose_recorder.html')

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
            if not pose_service.camera.is_opened:
                try:
                    pose_service.camera.open()
                except Exception as e:
                    socketio.emit('error', {'message': f'无法打开摄像头: {e}'})
                    return
            # 启动异步捕获和推理服务
            pose_service.start()
            # 启动Flask推送线程（推理是在此线程内触发的）
            threading.Thread(target=camera_thread, daemon=True).start()
            emit('status', {'message': '摄像头及推理服务已启动'})

    @socketio.on('stop_camera')
    def handle_stop_camera():
        """停止摄像头"""
        pose_service.is_running = False
        # 不关闭摄像头，保持打开状态以便重启
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
        """视频流推送线程 (Consumer)"""
        print("[FLASK] 视频推送线程启动")
        
        while pose_service.is_running:
            # 模型作为消费者，主动获取并处理最新帧
            # 若摄像头池子为空，此调用将阻塞等待
            processed_frame, state_name, poses, words_list = pose_service.capture_and_process()
            
            if processed_frame is not None:
                try:
                    # 编码为JPEG (镜像翻转可选)
                    display_frame = cv2.flip(processed_frame, 1)
                    ret, buffer = cv2.imencode('.jpg', display_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    if ret:
                        import base64
                        frame_base64 = base64.b64encode(buffer).decode('utf-8')
                        
                        # 发送数据
                        socketio.emit('frame_update', {
                            'image': frame_base64,
                            'state': state_name,
                            'poses_count': len(poses) if poses is not None else 0,
                            'instruction': words_list,
                            'stats': pose_service.get_stats(),
                            'fps': round(pose_service.stats['current_fps'], 1)
                        })
                except Exception as e:
                    print(f"[FLASK] 推送循环异常: {e}")
            else:
                time.sleep(0.01)

        print("[FLASK] 视频推送线程停止")

    # 调试工具路由
    @app.route('/api/send_mouse', methods=['POST'])
    def send_mouse():
        data = request.json
        url = data.get('url', '192.168.2.121')
        port = data.get('port', 80)
        words = data.get('words', 'a')
        
        print(f"[DEBUG] send_mouse called with url={url}, port={port}, words={words}")
        
        try:
            from UpperMachine.pose_estimation.sendcommand import send_command_timeout as send_command
            from UpperMachine.pose_estimation.bytes2command import bytes2command, mouse2command
            from UpperMachine.pose_estimation.state2bytes_vector import words2bytes
            
            if words == 'left_click':
                print("[DEBUG] Sending left click: press and release")
                # 左键点击：按下 + 释放
                cmd1 = mouse2command(-1)
                cmd2 = mouse2command(-2)
                send_command(url, port, cmd1)
                send_command(url, port, cmd2)
                hex_data = f"{cmd1.hex()} + {cmd2.hex()}"
                return jsonify({'status': 'success', 'result': 'Left click sent', 'hex': hex_data})
            elif words == 'mouse_left_click':
                print("[DEBUG] Sending left press")
                cmd = mouse2command(-1)
                send_command(url, port, cmd)
                return jsonify({'status': 'success', 'result': 'Left press sent', 'hex': cmd.hex()})
            elif words == 'move_left':
                print("[DEBUG] Sending move left: x=-10, y=0")
                # 左移光标：x=-10, y=0
                cmd = mouse2command(0, -10, 0)
                send_command(url, port, cmd)
                return jsonify({'status': 'success', 'result': 'Move left sent', 'hex': cmd.hex()})
            elif words == 'move_right':
                print("[DEBUG] Sending move right: x=10, y=0")
                # 右移光标：x=10, y=0
                cmd = mouse2command(0, 10, 0)
                send_command(url, port, cmd)
                return jsonify({'status': 'success', 'result': 'Move right sent', 'hex': cmd.hex()})
            elif words == 'move_left_release':
                print("[DEBUG] Sending move left and release: x=-10, y=0 + left release")
                # 左移后释放：左移 + 释放左键
                cmd1 = mouse2command(0, -10, 0)
                cmd2 = mouse2command(-2)
                send_command(url, port, cmd1)
                send_command(url, port, cmd2)
                hex_data = f"{cmd1.hex()} + {cmd2.hex()}"
                return jsonify({'status': 'success', 'result': 'Move left and release sent', 'hex': hex_data})
            elif words == 'move_right_release':
                print("[DEBUG] Sending move right and release: x=10, y=0 + left release")
                # 右移后释放：右移 + 释放左键
                cmd1 = mouse2command(0, 10, 0)
                cmd2 = mouse2command(-2)
                send_command(url, port, cmd1)
                send_command(url, port, cmd2)
                hex_data = f"{cmd1.hex()} + {cmd2.hex()}"
                return jsonify({'status': 'success', 'result': 'Move right and release sent', 'hex': hex_data})
            elif words == 'mouse_release':
                print("[DEBUG] Sending mouse release: release all mouse buttons")
                # 鼠标释放：释放所有鼠标按键
                cmd = mouse2command(-2)  # 释放左键
                send_command(url, port, cmd)
                return jsonify({'status': 'success', 'result': 'Mouse release sent', 'hex': cmd.hex()})
            else:
                print(f"[DEBUG] Processing general words: {words}")
                # 默认键盘或鼠标动作
                keyboard_bytes, mouse_actions = words2bytes(words)
                print(f"[DEBUG] keyboard_bytes: {keyboard_bytes}, mouse_actions: {mouse_actions}")
                
                hex_commands = []
                if keyboard_bytes:
                    command = bytes2command(keyboard_bytes)
                    print(f"[DEBUG] Sending keyboard command: {command.hex()}")
                    send_command(url, port, command)
                    hex_commands.append(f"KB:{command.hex()}")
                
                for action in mouse_actions:
                    command = mouse2command(action)
                    print(f"[DEBUG] Sending mouse command for action {action}: {command.hex()}")
                    send_command(url, port, command)
                    hex_commands.append(f"MS:{command.hex()}")
                
                hex_data = " | ".join(hex_commands) if hex_commands else "No commands"
                return jsonify({'status': 'success', 'result': f'Sent keyboard/mouse: {words}', 'hex': hex_data})
        except Exception as e:
            print(f"[ERROR] send_mouse failed: {str(e)}")
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

    @app.route('/api/detect_keypoints_batch', methods=['POST'])
    def detect_keypoints_batch():
        """批量检测关键点"""
        try:
            print("=== 开始批量检测关键点 ===")
            data = request.json
            frames = data.get('frames', [])
            print(f"接收到 {len(frames)} 帧数据")

            results = {}
            for i, frame_data in enumerate(frames):
                print(f"处理第 {i+1} 帧，索引: {frame_data.get('index', 'unknown')}")
                try:
                    # 解码base64图像
                    img_data_str = frame_data['imageData']
                    print(f"图像数据长度: {len(img_data_str)}")
                    if ',' in img_data_str:
                        img_data = base64.b64decode(img_data_str.split(',')[1])
                    else:
                        img_data = base64.b64decode(img_data_str)
                    print(f"解码后数据长度: {len(img_data)}")

                    nparr = np.frombuffer(img_data, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    print(f"图像解码成功，尺寸: {img.shape if img is not None else 'None'}")

                    if img is None:
                        print("图像解码失败")
                        results[frame_data['index']] = {}
                        continue

                    # 确保送入检测的图像为“镜像方向”
                    # 规则：前端如未镜像帧内容（frame_data.mirrored 为 False 或缺失），后端在此进行水平翻转
                    mirrored_flag = frame_data.get('mirrored', False)
                    if not mirrored_flag:
                        img = cv2.flip(img, 1)  # 1: 水平翻转

                    # 检测关键点
                    print("开始检测关键点...")
                    poses, _ = pose_service.estimator.infer(img, is_draw=False)
                    print(f"检测结果: poses = {poses}")

                    if poses is not None and len(poses) > 0:
                        print(f"检测到 {len(poses)} 个姿势")
                        # 转换为字典格式
                        keypoints_dict = pose_service.estimator.pose2dict(poses)
                        print(f"关键点字典: {keypoints_dict}")

                        # 将numpy数组转换为Python列表，确保JSON序列化
                        keypoints_dict = convert_numpy_to_list(keypoints_dict)
                        print(f"转换后关键点字典: {keypoints_dict}")
                        results[frame_data['index']] = keypoints_dict
                    else:
                        print("未检测到姿势")
                        results[frame_data['index']] = {}

                except Exception as frame_error:
                    print(f"处理第 {i+1} 帧时出错: {str(frame_error)}")
                    results[frame_data['index']] = {}

            print(f"批量检测完成，共处理 {len(results)} 帧")
            print(f"返回结果: {results}")
            return jsonify({'success': True, 'keypoints': results})
        except Exception as e:
            print(f"批量检测关键点出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': str(e)})

    @app.route('/api/save_pose', methods=['POST'])
    def save_pose():
        """保存姿势配置"""
        try:
            data = request.json
            # 规范化 pose_img 字段（可选）
            pose_img = (data.get('pose_img') or '').strip()
            if pose_img:
                # 如果是以 /static/ 开头，去掉该前缀
                if pose_img.startswith('/static/'):
                    pose_img = pose_img[len('/static/'):]
                # 允许传入 Images/xxx 或 Source/Images/xxx 或仅文件名
                if pose_img.startswith('Images/'):
                    pose_img = pose_img[len('Images/'):]
                elif pose_img.startswith('Source/Images/'):
                    pose_img = pose_img[len('Source/Images/'):]
                else:
                    # 如果包含路径，仅保留文件名
                    if '/' in pose_img:
                        pose_img = pose_img.split('/')[-1]
                # 最终统一保存为 Source/Images/<filename>
                pose_img = f"Source/Images/{pose_img}"
            data['pose_img'] = pose_img
            
            # 读取现有配置
            with open('Source/configs.json', 'r', encoding='utf-8') as f:
                configs = json.load(f)
            
            # 检查是否已存在相同索引的姿势
            existing_index = None
            for i, pose in enumerate(configs):
                if pose['index'] == data['index']:
                    existing_index = i
                    break
            
            # 更新或添加姿势
            if existing_index is not None:
                # 如果没有传 pose_img，保留原有值
                if not data.get('pose_img') and configs[existing_index].get('pose_img'):
                    data['pose_img'] = configs[existing_index]['pose_img']
                configs[existing_index] = data
            else:
                # 新姿势：pose_img 字段已在前面归一化
                configs.append(data)
            
            # 按索引排序
            configs.sort(key=lambda x: x['index'])
            
            # 保存配置
            with open('Source/configs.json', 'w', encoding='utf-8') as f:
                json.dump(configs, f, indent=4, ensure_ascii=False)
            
            return jsonify({'success': True, 'message': '姿势保存成功'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

    @app.route('/api/delete_pose', methods=['POST'])
    def delete_pose_post():
        """删除指定索引的姿势配置"""
        try:
            data = request.json or {}
            if 'index' not in data:
                return jsonify({'success': False, 'message': '缺少 index 参数'})

            target_index = data['index']

            # 读取现有配置
            with open('Source/configs.json', 'r', encoding='utf-8') as f:
                configs = json.load(f)

            # 查找并删除
            new_configs = [p for p in configs if p.get('index') != target_index]

            if len(new_configs) == len(configs):
                return jsonify({'success': False, 'message': f'未找到索引为 {target_index} 的姿势'})

            # 保存更新后的配置
            new_configs.sort(key=lambda x: x['index'])
            with open('Source/configs.json', 'w', encoding='utf-8') as f:
                json.dump(new_configs, f, indent=4, ensure_ascii=False)

            return jsonify({'success': True, 'message': '删除成功'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

    @app.route('/api/get_poses')
    def get_poses():
        """获取所有姿势"""
        try:
            with open('Source/configs.json', 'r', encoding='utf-8') as f:
                configs = json.load(f)
            return jsonify(configs)
        except Exception as e:
            return jsonify([])

    @app.route('/api/get_pose/<int:pose_index>')
    def get_pose(pose_index):
        """获取特定姿势"""
        try:
            with open('Source/configs.json', 'r', encoding='utf-8') as f:
                configs = json.load(f)
            
            for pose in configs:
                if pose['index'] == pose_index:
                    return jsonify(pose)
            
            return jsonify({'error': '姿势不存在'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/delete_pose/<int:pose_index>', methods=['DELETE'])
    def delete_pose(pose_index):
        """删除姿势"""
        try:
            # 读取现有配置
            with open('Source/configs.json', 'r', encoding='utf-8') as f:
                configs = json.load(f)
            
            # 找到并删除姿势
            new_configs = [pose for pose in configs if pose['index'] != pose_index]
            
            if len(new_configs) == len(configs):
                return jsonify({'success': False, 'message': '姿势不存在'})
            
            # 保存配置
            with open('Source/configs.json', 'w', encoding='utf-8') as f:
                json.dump(new_configs, f, indent=4, ensure_ascii=False)
            
            return jsonify({'success': True, 'message': '姿势删除成功'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})


    @app.route('/api/render_keypoints', methods=['POST'])
    def render_keypoints():
        """渲染带有关键点的图像"""
        try:
            data = request.json
            frame_data = data.get('frame', {})
            
            if not frame_data or 'imageData' not in frame_data:
                return jsonify({'success': False, 'message': '缺少图像数据'})
            
            # 解码base64图像
            img_data_str = frame_data['imageData']
            if ',' in img_data_str:
                img_data = base64.b64decode(img_data_str.split(',')[1])
            else:
                img_data = base64.b64decode(img_data_str)
            
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return jsonify({'success': False, 'message': '图像解码失败'})
            
            # 根据前端标记，保证送入绘制的是镜像方向
            mirrored_flag = frame_data.get('mirrored', False)
            if not mirrored_flag:
                img = cv2.flip(img, 1)

            # 使用estimator进行检测并绘制关键点
            poses, processed_frame = pose_service.estimator.infer(img, is_draw=True)
            
            if processed_frame is not None:
                # 将处理后的图像编码为base64
                _, buffer = cv2.imencode('.jpg', processed_frame)
                img_base64 = base64.b64encode(buffer).decode('utf-8')
                img_data_url = f'data:image/jpeg;base64,{img_base64}'
                
                return jsonify({
                    'success': True, 
                    'imageData': img_data_url,
                    'hasPoses': poses is not None and len(poses) > 0
                })
            else:
                return jsonify({'success': False, 'message': '关键点渲染失败'})
                
        except Exception as e:
            print(f"渲染关键点出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': str(e)})

