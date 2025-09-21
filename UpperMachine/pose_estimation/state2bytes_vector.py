import json

words2bytes_dict = {
    # 字母键 (a-z) - USB HID 键盘扫描码
    'a': 0x04, 'b': 0x05, 'c': 0x06, 'd': 0x07, 'e': 0x08, 'f': 0x09,
    'g': 0x0A, 'h': 0x0B, 'i': 0x0C, 'j': 0x0D, 'k': 0x0E, 'l': 0x0F,
    'm': 0x10, 'n': 0x11, 'o': 0x12, 'p': 0x13, 'q': 0x14, 'r': 0x15,
    's': 0x16, 't': 0x17, 'u': 0x18, 'v': 0x19, 'w': 0x1A, 'x': 0x1B,
    'y': 0x1C, 'z': 0x1D,

    # 数字键 (0-9)
    '1': 0x1E, '2': 0x1F, '3': 0x20, '4': 0x21, '5': 0x22, '6': 0x23,
    '7': 0x24, '8': 0x25, '9': 0x26, '0': 0x27,

    # 功能键
    'f1': 0x3A, 'f2': 0x3B, 'f3': 0x3C, 'f4': 0x3D, 'f5': 0x3E, 'f6': 0x3F,
    'f7': 0x40, 'f8': 0x41, 'f9': 0x42, 'f10': 0x43, 'f11': 0x44, 'f12': 0x45,

    # 控制键
    'enter': 0x28, 'esc': 0x29, 'backspace': 0x2A, 'tab': 0x2B, 'space': 0x2C,
    'caps_lock': 0x39,

    # 修饰键 (通常不需要单独映射，因为由硬件处理)
    'left_ctrl': 0xE0, 'left_shift': 0xE1, 'left_alt': 0xE2, 'left_gui': 0xE3,
    'right_ctrl': 0xE4, 'right_shift': 0xE5, 'right_alt': 0xE6, 'right_gui': 0xE7,

    # 方向键
    'up': 0x52, 'down': 0x51, 'left': 0x50, 'right': 0x4F,

    # 其他常用键
    '-': 0x2D, '=': 0x2E, '[': 0x2F, ']': 0x30, '\\': 0x31, ';': 0x33,
    "'": 0x34, '`': 0x35, ',': 0x36, '.': 0x37, '/': 0x38,

    # 小键盘
    'num_lock': 0x53, 'kp_/': 0x54, 'kp_*': 0x55, 'kp_-': 0x56, 'kp_+': 0x57,
    'kp_enter': 0x58, 'kp_1': 0x59, 'kp_2': 0x5A, 'kp_3': 0x5B, 'kp_4': 0x5C,
    'kp_5': 0x5D, 'kp_6': 0x5E, 'kp_7': 0x5F, 'kp_8': 0x60, 'kp_9': 0x61,
    'kp_0': 0x62, 'kp_.': 0x63,

    # 鼠标操作 - 使用特殊标识符 (负数表示鼠标操作)
    "mouse_left_click": -1,      # 鼠标左键按下
    "mouse_left_release": -2,    # 鼠标左键释放
    "mouse_right_click": -3,     # 鼠标右键按下
    "mouse_right_release": -4,   # 鼠标右键释放
    "mouse_middle_click": -5,    # 鼠标中键按下
    "mouse_middle_release": -6,  # 鼠标中键释放
    "mouse_wheel_up": -7,        # 滚轮向上
    "mouse_wheel_down": -8,      # 滚轮向下
}

with open("Source/configs.json", "r", encoding="utf-8") as f:
    configs_data = json.load(f)
    mapper_list = [{"action": [pose["index"]], "keys": pose["keys"]} for pose in configs_data]

def state2words(state):
    words_list = []
    for i in range(len(mapper_list)):
        action_list = mapper_list[i]["action"]
        keys_list = mapper_list[i]["keys"]
        # 若action_list中每个元素都在state中，则将keys_list添加到words_list中
        if all(item in state for item in action_list):
            words_list += keys_list
    words_list = list(set(words_list))
    return words_list

    # # 注释掉的旧代码 - 保留作为参考
    # # state to list of words
    # if 11 in state:
    #     words_list.append('s')
    # elif 3 in state and 4 in state: # 向前
    #     words_list.append('w')
    # elif 3 in state:
    #     words_list.append('d')
    # elif 4 in state:
    #     words_list.append('a')
    # else:
    #     pass
    #
    # # 左右
    # if 1 in state:
    #     words_list.append('j') # 平A
    # if 2 in state:
    #     words_list.append('k') # 闪避
    #
    # if 9 in state:
    #     words_list.append('e') # e技能
    # if 10 in state:
    #     words_list.append('q') # q技能
    #
    # if 5 in state:
    #     words_list.append('i') # 确认
    # if 6 in state:
    #     words_list.append('o') # 取消
    #
    # if 7 in state:
    #     words_list.append('n') # 向右转
    # if 8 in state:
    #     words_list.append('m') # 向左转

    # return words_list  # 删除这个重复的return语句

def words2bytes(words_list):
    """
    将按键名称列表转换为字节列表
    支持键盘和鼠标操作的混合
    """
    keyboard_bytes = []
    mouse_actions = []

    for word in words_list:
        code = words2bytes_dict.get(word, 0x00)
        if code < 0:  # 负数表示鼠标操作
            mouse_actions.append(code)
        else:  # 正数或0表示键盘操作
            keyboard_bytes.append(code)

    return keyboard_bytes, mouse_actions


def state2bytes(state):
    """
    将状态转换为键盘和鼠标的字节数据
    返回 (keyboard_bytes, mouse_actions) 元组
    鼠标命令格式：
    - 命令字段：0x04
    - 数据长度：至少7字节
    """
    words_list = state2words(state)
    keyboard_bytes, mouse_actions = words2bytes(words_list)

    return keyboard_bytes, mouse_actions