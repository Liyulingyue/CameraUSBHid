def bytes2command(data_list):
    """
    生成符合指定协议格式的二进制命令包 (键盘)

    参数:
        data_list (list): 要发送的数据列表，每个元素应为0-255的整数

    返回:
        bytes: 完整的二进制命令包
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
    根据鼠标动作和坐标生成完整的 USB 鼠标命令包
    数据包格式：
    - 帧头 (2字节): 0x57, 0xAB
    - 地址 (1字节): 0x00
    - 命令 (1字节): 0x04 (鼠标命令)
    - 数据长度 (1字节): 0x07 (固定7字节)
    - 数据 (7字节): USB 绝对鼠标数据包
    - 校验和 (1字节): 累加和
    """
    # 生成7字节鼠标数据包
    data_packet = [0x02]  # 第1个字节固定为0x02

    # 初始化默认值
    button_value = 0x00  # 鼠标按键值
    x_axis = x & 0xFFFF  # X轴坐标值，限制为16位
    y_axis = y & 0xFFFF  # Y轴坐标值，限制为16位
    wheel = 0x00  # 滚轮滚动齿数

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

    # 将X轴和Y轴坐标值分解为低字节和高字节
    x_low = x_axis & 0xFF
    x_high = (x_axis >> 8) & 0xFF
    y_low = y_axis & 0xFF
    y_high = (y_axis >> 8) & 0xFF

    # 构造7字节数据包
    data_packet.append(button_value)  # 第2个字节：鼠标按键值
    data_packet.append(x_low)         # 第3个字节：X轴低字节
    data_packet.append(x_high)        # 第4个字节：X轴高字节
    data_packet.append(y_low)         # 第5个字节：Y轴低字节
    data_packet.append(y_high)        # 第6个字节：Y轴高字节
    data_packet.append(wheel)         # 第7个字节：滚轮滚动齿数

    # 构造完整命令包
    header = [0x57, 0xAB]  # 帧头
    addr = 0x00            # 地址
    cmd = 0x04             # 命令 (鼠标命令)
    data_length = 0x07     # 数据长度 (固定7字节)

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

    # 鼠标命令示例
    mouse_command = mouse2command(-1)  # 左键按下
    print("鼠标命令:", bytes(mouse_command).hex(' ').upper())
    # 输出示例: 02 01 00 00 00 00 01

    mouse_command = mouse2command(-7)  # 滚轮向上
    print("鼠标命令:", bytes(mouse_command).hex(' ').upper())
    # 输出示例: 02 00 00 00 00 00 01

    mouse_command = mouse2command(-8)  # 滚轮向下
    print("鼠标命令:", bytes(mouse_command).hex(' ').upper())
    # 输出示例: 02 00 00 00 00 00 FF