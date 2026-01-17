import socket

import select

last_command = ""


# 使用ESP32Cam作为服务器，端口为80，服务器只会接收一次，然后就断开，不会保持连接，所以每次都需要创建一个socket
def send_command(server_ip='192.168.2.121', port=80, command="", ifencode=False, ignore_cache=False):
    global last_command
    if not ignore_cache and last_command == command:
        return
    else:
        last_command = command

    # 创建一个TCP/IP套接字
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 连接到服务器
        sock.connect((server_ip, port))
        command = command.encode() if ifencode else command # 是否进行二进制转码
        sock.sendall(command)
    finally:
        # 关闭套接字
        sock.close()

def send_command_timeout(server_ip='192.168.2.121', port=80, command="", timeout=1, ifencode=False, ignore_cache=False):
    global last_command
    if not ignore_cache and last_command == command:
        return
    else:
        last_command = command

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(0)  # 设置为非阻塞模式

    try:
        # 尝试连接到服务器
        sock.connect_ex((server_ip, port))
        # 使用select来等待连接完成，超时为timeout秒
        readable, writable, exceptional = select.select([], [sock], [], timeout)

        if sock in writable:
            command = command.encode() if ifencode else command # 是否进行二进制转码
            sock.sendall(command)
        else:
            # 连接超时
            raise socket.timeout("Connection timed out")

    except socket.error as e:
        # 连接失败（包括超时）
        print(f"Connection error: {e}")

    finally:
        # 关闭套接字
        sock.close()