"""
基于Flask和Socket.IO的实时摄像头姿态检测应用
提供更灵活的自定义功能和更好的性能控制
"""

from flask import Flask
from flask_socketio import SocketIO

# 导入路由
from UpperMachine.flask.routes import register_routes

app = Flask(__name__, template_folder='GUI/flask/templates', static_folder='Source', static_url_path='/static')
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 注册路由
register_routes(app, socketio)

if __name__ == '__main__':
    # 创建模板目录
    import os
    os.makedirs('templates', exist_ok=True)
    
    # 运行应用
    print("启动Flask应用...")
    print("访问 http://localhost:5000 查看实时姿态检测")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)