from tabnanny import check


def generate_command(data_list):
    """
    生成符合指定协议格式的二进制命令包

    参数:
        data_list (list): 要发送的数据列表，每个元素应为0-255的整数

    返回:
        bytes: 完整的二进制命令包
    """
    data_list = [0x00] if len(data_list) == 0 else data_list

    # 固定帧头 (2字节)
    header = [0x57, 0xAB]

    # 地址字段 (1字节)
    addr = 0x00

    # 命令字段 (1字节)
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

# 使用示例
if __name__ == "__main__":
    # 示例1：发送3字节数据 [0x01, 0x02, 0x03]
    example_data = [0x04]
    command = generate_command(example_data)
    print("生成命令:", command.hex(' ').upper())
    # 输出: 57 AB 00 82 03 01 02 03 8B

    # 示例2：发送空数据
    empty_data = []
    command = generate_command(empty_data)
    print("生成命令:", command.hex(' ').upper())
    # 输出: 57 AB 00 82 00 82

    # 示例3：边界值测试 (255)
    edge_case = [0xFF]
    command = generate_command(edge_case)
    print("生成命令:", command.hex(' ').upper())
    # 输出: 57 AB 00 82 01 FF 82