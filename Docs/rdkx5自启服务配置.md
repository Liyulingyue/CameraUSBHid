# RDK X5 应用程序开机自启动配置指南

本项目提供了 `systemd` 配置文件，用于在 Linux 系统（如 RDK X5）上实现前后端服务的开机自启动。

## 1. 服务配置文件说明

### 后端服务 (`camerahid-backend.service`)
该服务负责运行 Flask 后端，处理姿态检测逻辑。
文件路径：`/etc/systemd/system/camerahid-backend.service`

```ini
[Unit]
Description=Camera USB HID Backend Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/CameraUSBHid
ExecStart=/usr/bin/python3 /root/CameraUSBHid/flask_app.py
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

### 前端服务 (`camerahid-frontend.service`)
该服务负责运行 Vite 前端界面。
文件路径：`/etc/systemd/system/camerahid-frontend.service`

```ini
[Unit]
Description=Camera USB HID Frontend Service
After=network.target
Requires=camerahid-backend.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/CameraUSBHid/frontend
ExecStart=/usr/bin/npm run dev -- --host
Restart=always

[Install]
WantedBy=multi-user.target
```

## 2. 启用方法

执行以下命令以重新加载配置并设置开机自启：

```bash
# 重新加载 systemd 配置
sudo systemctl daemon-reload

# 启用开机自启
sudo systemctl enable camerahid-backend.service
sudo systemctl enable camerahid-frontend.service

# 立即启动服务
sudo systemctl start camerahid-backend.service
sudo systemctl start camerahid-frontend.service
```

## 3. 常用管理命令

*   **查看状态**：`systemctl status camerahid-backend`
*   **查看日志**：`journalctl -u camerahid-backend -f`
*   **重启服务**：`systemctl restart camerahid-backend`
*   **停止服务**：`systemctl stop camerahid-backend`

## 4. 开发与调试建议

在进行代码修改或手动调试时，建议先停掉自动运行的服务，以避免**端口冲突**（端口 5000 和 5173）并方便查看实时日志。

### 开发模式工作流程：
1.  **停止背景服务**：
    ```bash
    sudo systemctl stop camerahid-backend camerahid-frontend
    ```
2.  **手动运行调试**：
    *   后端：`python flask_app.py`
    *   前端：`cd frontend && npm run dev`
3.  **恢复自启服务**：
    调试完毕后，您不需要执行复杂的指令，只需执行以下命令**重启**服务即可让新代码在后台运行：
    ```bash
    sudo systemctl restart camerahid-backend camerahid-frontend
    ```
    *注：如果您直接**重启机器**，系统也会自动按照最新的代码启动服务。*

## 5. 注意事项
*   确保路径 `/root/CameraUSBHid` 正确。
*   如果使用虚拟环境，请将 `ExecStart` 中的 python 路径指向虚拟环境的 python 解释器。
*   后端代码中 `socketio.run` 需包含 `allow_unsafe_werkzeug=True` 以防在后台运行时报错。
