"""
基于Flask和Socket.IO的实时摄像头姿态检测应用
提供更灵活的自定义功能和更好的性能控制
"""

from flask import Flask, send_from_directory
from flask_socketio import SocketIO
import os

# 导入路由
from UpperMachine.flask.routes import register_routes

# 自动定位前端目录
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), 'frontend', 'dist')

app = Flask(__name__, 
            template_folder='GUI/flask/templates', 
            static_folder=FRONTEND_DIST if os.path.exists(FRONTEND_DIST) else 'Source', 
            static_url_path='/static')
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 注册路由
register_routes(app, socketio)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path and os.path.exists(os.path.join(FRONTEND_DIST, path)):
        return send_from_directory(FRONTEND_DIST, path)
    if os.path.exists(os.path.join(FRONTEND_DIST, 'index.html')):
        return send_from_directory(FRONTEND_DIST, 'index.html')
    # 退化逻辑：如果没有编译前端，尝试渲染旧模板（如果路由还没冲突）
    from flask import render_template
    try:
        return render_template('index.html')
    except:
        return "React 前端尚未构建。请运行 'cd frontend && npm run build'。"

if __name__ == '__main__':
    # 创建模板目录
    import os
    os.makedirs('templates', exist_ok=True)
    
    # 运行应用
    print("启动Flask应用...")
    print("访问 http://localhost:5000 查看实时姿态检测")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)