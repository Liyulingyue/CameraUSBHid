words2bytes_dict = {
    's': 0x16,
    'w': 0x1A,
    'd': 0x07,
    'a': 0x04,
    'j': 0x0D,
    'k': 0x0E,
    'e': 0x08,
    'q': 0x14,
    'i': 0x0C,
    'o': 0x12,
    'n': 0x11,
    'm': 0x10,
}
def state2words(state):
    words_list = []

    # state to list of words
    if 11 in state:
        words_list.append('s')
    elif 3 in state and 4 in state: # 向前
        words_list.append('w')
    elif 3 in state:
        words_list.append('d')
    elif 4 in state:
        words_list.append('a')
    else:
        pass

    # 左右
    if 1 in state:
        words_list.append('j') # 平A
    if 2 in state:
        words_list.append('k') # 闪避

    if 9 in state:
        words_list.append('e') # e技能
    if 10 in state:
        words_list.append('q') # q技能

    if 5 in state:
        words_list.append('i') # 确认
    if 6 in state:
        words_list.append('o') # 取消

    if 7 in state:
        words_list.append('n') # 向右转
    if 8 in state:
        words_list.append('m') # 向左转

    return words_list

def words2bytes(words_list):
    bytes_list = [words2bytes_dict.get(x, 0x00) for x in words_list]

    return bytes_list

def state2bytes(state):
    words_list = state2words(state)
    bytes_list = words2bytes(words_list)


    return bytes_list