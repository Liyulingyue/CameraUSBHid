import time
import socket
from UpperMachine.pose_estimation.bytes2command import bytes2command, mouse2command

# ================= 配置区 =================
# 目标设备的 IP 地址，请确保与你的 ESP32/控制器 IP 一致
TARGET_IP = '192.168.50.42' 
PORT = 80
# ==========================================

def send_raw_command(packet):
    """
    直接通过 TCP 发送原始字节流到控制器。
    绕过现有的缓存机制，确保连续的坐标移动指令能被正常发送。
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0) # 设置 1 秒超时
            s.connect((TARGET_IP, PORT))
            s.sendall(packet)
    except Exception as e:
        print(f"发送指令失败: {e}")

def main():
    print(f"--- 自动化脚本启动 ---")
    print(f"目标 IP: {TARGET_IP}:{PORT}")
    
    # 1. 发送 'a' 键盘按下指令
    # 扫描码 0x04 对应键盘上的 'a' 键
    print(">>> 步骤 1: 发送 'a' 键按下")
    kb_press_cmd = bytes2command([0x04])
    send_raw_command(kb_press_cmd)
    
    # 2. 鼠标向左移动 3 秒
    # 在 bytes2command.py 中，action=-9 被映射为相对左移 10 像素
    print(">>> 步骤 2: 鼠标向左连续移动 (3秒)...")
    start_time = time.time()
    while time.time() - start_time < 3:
        mouse_left_cmd = mouse2command(-9)
        send_raw_command(mouse_left_cmd)
        time.sleep(0.05) # 以 20Hz 的频率发送移动指令
        
    # 3. 鼠标向右移动 3 秒
    # 在 bytes2command.py 中，action=-10 被映射为相对右移 10 像素
    print(">>> 步骤 3: 鼠标向右连续移动 (3秒)...")
    start_time = time.time()
    while time.time() - start_time < 3:
        mouse_right_cmd = mouse2command(-10)
        send_raw_command(mouse_right_cmd)
        time.sleep(0.05)

    # 4. 释放 'a' 键盘按键
    # 发送空列表会生成全 0 的键盘报文，从而释放所有按键
    print(">>> 步骤 4: 释放 'a' 键并停止")
    kb_release_cmd = bytes2command([])
    send_raw_command(kb_release_cmd)
    
    # 可选：确保鼠标按键也处于释放状态
    mouse_release_cmd = mouse2command(-11)
    send_raw_command(mouse_release_cmd)
    
    print("--- 任务执行完毕 ---")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] 用户中断，正在尝试清理按键状态...")
        # 紧急释放所有按键
        try:
            emergency_release = bytes2command([])
            send_raw_command(emergency_release)
        except:
            pass
