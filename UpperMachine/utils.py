"""
UpperMachine 模块的辅助函数
"""

import numpy as np
import os
import re


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


def get_latest_config_path(base_dir="Source"):
    """
    搜索并返回最新的配置文件路径。
    - configs.yml 作为 data_num=0
    - configs_{data_num}.py 文件，取 data_num 最大的
    如果没有找到，返回默认的 configs.yml
    """
    if not os.path.exists(base_dir):
        return os.path.join(base_dir, "configs.yml")
    
    files = os.listdir(base_dir)
    configs = []
    
    for f in files:
        if f == "configs.yml":
            configs.append((0, os.path.join(base_dir, f)))
        elif f.startswith("configs_") and f.endswith(".json"):
            match = re.match(r"configs_(\d+)\.json", f)
            if match:
                data_num = int(match.group(1))
                configs.append((data_num, os.path.join(base_dir, f)))
    
    if not configs:
        return os.path.join(base_dir, "configs.yml")
    
    # 按 data_num 降序排序，取最大的
    configs.sort(key=lambda x: x[0], reverse=True)
    return configs[0][1]