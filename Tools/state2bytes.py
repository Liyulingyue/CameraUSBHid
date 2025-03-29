def state2bytes(state):
    return bytes([int(x) for x in state.split()])