"""
UpperMachine 模块的辅助函数
"""

import numpy as np


def convert_numpy_to_list(obj):
    """
    将numpy数组转换为Python列表，确保JSON序列化

    Args:
        obj: 要转换的对象，可以是numpy数组、字典、列表或其他类型

    Returns:
        转换后的对象，其中所有numpy数组都被转换为Python列表
    """
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_to_list(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_list(item) for item in obj]
    else:
        return obj