def bytes2command(data_list):
    """
    生成符合指定协议格式的二进制命令包 (键盘)

    参数:
        data_list (list): 要发送的数据列表，每个元素应为0-255的整数

    """
    data_list = [0x00] if len(data_list) == 0 else data_list
    data_list = [0x00] * (8 - len(data_list)) + data_list # 补零，避免无反应

    # 固定帧头 (2字节)
    header = [0x57, 0xAB]

    # 地址字段 (1字节)
    addr = 0x00

    # 命令字段 (1字节) - 0x02 表示键盘命令
    cmd = 0x02

    # 数据长度字段 (1字节)
    data_length = len(data_list)

    # 转换数据列表为字节 (自动处理0-255范围)
    data_bytes = data_list

    # 计算校验和：地址 + 命令 + 数据长度 + 所有数据字节的和 (1字节)
    checksum = (sum(header) + addr + cmd + data_length + sum(data_bytes)) % 256
    # 组装完整数据包
    packet = (bytes(header) + # 帧头
        bytes([addr, cmd, data_length]) +  # 地址、命令、长度
        bytes(data_bytes) +              # 数据部分
        bytes([checksum])         # 校验和
    )
    print(packet)

    return packet


def mouse2command(action, x=0, y=0):
    """
    根据鼠标动作和坐标生成完整的 USB 鼠标命令包 (相对模式)
    数据包格式：
    - 帧头 (2字节): 0x57, 0xAB
    - 地址 (1字节): 0x00
    - 命令 (1字节): 0x05 (鼠标相对命令)
    - 数据长度 (1字节): 0x05 (相对模式5字节)
    - 数据 (5字节): USB 相对鼠标数据包
      - 第1字节：固定为1
      - 第2字节：按键状态 (bit0:左键, bit1:右键, bit2:中键)
      - 第3字节：X轴相对移动 (-127~127)
      - 第4字节：Y轴相对移动 (-127~127)
      - 第5字节：滚轮相对移动 (-127~127)
    - 校验和 (1字节): 累加和

    # 鼠标命令示例
    mouse_command = mouse2command(-1)  # 左键按下
    print("鼠标左键按下命令:", bytes(mouse_command).hex(' ').upper())
    # 输出示例: 57 AB 00 05 05 01 01 00 00 00 XX

    mouse_command = mouse2command(-2)  # 左键弹起
    print("鼠标左键弹起命令:", bytes(mouse_command).hex(' ').upper())
    # 输出示例: 57 AB 00 05 05 01 00 00 00 00 XX

    mouse_command = mouse2command(0, -10, 0)  # 鼠标左移10像素
    print("鼠标左移命令:", bytes(mouse_command).hex(' ').upper())
    # 输出示例: 57 AB 00 05 05 01 00 F6 00 00 XX

    mouse_command = mouse2command(0, 10, 0)  # 鼠标右移10像素
    print("鼠标右移命令:", bytes(mouse_command).hex(' ').upper())
    # 输出示例: 57 AB 00 05 05 01 00 0A 00 00 XX

    mouse_command = mouse2command(-7)  # 滚轮向上
    print("鼠标滚轮向上命令:", bytes(mouse_command).hex(' ').upper())
    # 输出示例: 57 AB 00 05 05 01 00 00 00 01 XX

    mouse_command = mouse2command(-8)  # 滚轮向下
    print("鼠标滚轮向下命令:", bytes(mouse_command).hex(' ').upper())
    # 输出示例: 57 AB 00 05 05 01 00 00 00 FF XX

    mouse_command = mouse2command(0, 10, -5)  # 相对移动：右移10像素，上移5像素
    print("鼠标相对移动命令:", bytes(mouse_command).hex(' ').upper())
    # 输出示例: 57 AB 00 05 05 01 00 0A FB 00 XX bytes: 完整的二进制命令包
    
    """
    # 初始化默认值
    button_value = 0x00  # 鼠标按键值
    x_rel = 0            # X轴相对移动
    y_rel = 0            # Y轴相对移动
    wheel = 0x00         # 滚轮滚动齿数

    # 根据动作类型设置数据包内容
    if action == -1:  # 鼠标左键按下
        button_value = 0x01
    elif action == -2:  # 鼠标左键释放
        button_value = 0x00
    elif action == -3:  # 鼠标右键按下
        button_value = 0x02
    elif action == -4:  # 鼠标右键释放
        button_value = 0x00
    elif action == -5:  # 鼠标中键按下
        button_value = 0x04
    elif action == -6:  # 鼠标中键释放
        button_value = 0x00
    elif action == -7:  # 滚轮向上
        wheel = 0x01
    elif action == -8:  # 滚轮向下
        wheel = 0xFF
    elif action == -9:  # 鼠标左移
        x_rel = -10  # 左移10像素
    elif action == -10:  # 鼠标右移
        x_rel = 10   # 右移10像素
    elif action == -11:  # 鼠标释放（所有按键）
        button_value = 0x00  # 释放所有按键
    else:  # 相对移动
        # 将输入的x,y作为相对移动值，限制在-127~127范围内
        x_rel = max(-127, min(127, x))
        y_rel = max(-127, min(127, y))

    # 构造5字节相对鼠标数据包
    data_packet = [
        0x01,               # 第1字节：固定为1
        button_value,       # 第2字节：按键状态
        x_rel & 0xFF,       # 第3字节：X轴相对移动 (有符号字节)
        y_rel & 0xFF,       # 第4字节：Y轴相对移动 (有符号字节)
        wheel               # 第5字节：滚轮相对移动
    ]

    # 构造完整命令包
    header = [0x57, 0xAB]  # 帧头
    addr = 0x00            # 地址
    cmd = 0x05             # 命令 (鼠标相对命令)
    data_length = 0x05     # 数据长度 (相对模式5字节)

    # 计算校验和：地址 + 命令 + 数据长度 + 所有数据字节的和
    checksum = (sum(header) + addr + cmd + data_length + sum(data_packet)) % 256

    # 组装完整数据包
    packet = (bytes(header) +           # 帧头
              bytes([addr, cmd, data_length]) +  # 地址、命令、长度
              bytes(data_packet) +      # 数据部分
              bytes([checksum])         # 校验和
    )

    return packet

# 使用示例
if __name__ == "__main__":
    # 键盘命令示例 (bytes2command)
    print("=== 键盘命令测试 ===")
    # 示例1：发送3字节数据 [0x01, 0x02, 0x03]
    example_data = [0x04]
    command = bytes2command(example_data)
    print("生成命令:", command.hex(' ').upper())
    # 输出: 57 AB 00 82 03 01 02 03 8B

    # 示例2：发送空数据
    empty_data = []
    command = bytes2command(empty_data)
    print("生成命令:", command.hex(' ').upper())
    # 输出: 57 AB 00 82 00 82

    # 示例3：边界值测试 (255)
    edge_case = [0xFF]
    command = bytes2command(edge_case)
    print("生成命令:", command.hex(' ').upper())
    # 输出: 57 AB 00 82 01 FF 82

    # 鼠标命令示例 (mouse2command)
    print("\n=== 鼠标命令测试 ===")
    mouse_command = mouse2command(-1)  # 左键按下
    print("鼠标左键按下命令:", bytes(mouse_command).hex(' ').upper())
    # 输出示例: 57 AB 00 05 05 01 01 00 00 00 XX

    mouse_command = mouse2command(-2)  # 左键弹起
    print("鼠标左键弹起命令:", bytes(mouse_command).hex(' ').upper())
    # 输出示例: 57 AB 00 05 05 01 00 00 00 00 XX

    mouse_command = mouse2command(0, -10, 0)  # 鼠标左移10像素
    print("鼠标左移命令:", bytes(mouse_command).hex(' ').upper())
    # 输出示例: 57 AB 00 05 05 01 00 F6 00 00 XX

    mouse_command = mouse2command(0, 10, 0)  # 鼠标右移10像素
    print("鼠标右移命令:", bytes(mouse_command).hex(' ').upper())
    # 输出示例: 57 AB 00 05 05 01 00 0A 00 00 XX

    mouse_command = mouse2command(-7)  # 滚轮向上
    print("鼠标滚轮向上命令:", bytes(mouse_command).hex(' ').upper())
    # 输出示例: 57 AB 00 05 05 01 00 00 00 01 XX

    mouse_command = mouse2command(-8)  # 滚轮向下
    print("鼠标滚轮向下命令:", bytes(mouse_command).hex(' ').upper())
    # 输出示例: 57 AB 00 05 05 01 00 00 00 FF XX

    mouse_command = mouse2command(0, 10, -5)  # 相对移动：右移10像素，上移5像素
    print("鼠标相对移动命令:", bytes(mouse_command).hex(' ').upper())
    # 输出示例: 57 AB 00 05 05 01 00 0A FB 00 XX bytes: 完整的二进制命令包

    mouse_command = mouse2command(-9)  # 鼠标左移
    print("鼠标左移命令:", bytes(mouse_command).hex(' ').upper())
    # 输出示例: 57 AB 00 05 05 01 00 F6 00 00 XX

    mouse_command = mouse2command(-10)  # 鼠标右移
    print("鼠标右移命令:", bytes(mouse_command).hex(' ').upper())
    # 输出示例: 57 AB 00 05 05 01 00 0A 00 00 XX

    mouse_command = mouse2command(-11)  # 鼠标释放
    print("鼠标释放命令:", bytes(mouse_command).hex(' ').upper())
    # 输出示例: 57 AB 00 05 05 05 01 00 00 00 00 XX