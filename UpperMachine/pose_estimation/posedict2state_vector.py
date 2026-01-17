import numpy as np
import json
import math
import os
import yaml

from UpperMachine.utils import get_latest_config_path

# 获取热重载配置
def _load_hot_reload_setting():
    try:
        with open("Source/flask_config.yml", 'r') as f:
            config = yaml.safe_load(f)
            return config.get('hot_reload', False)
    except:
        return False

HOT_RELOAD_ENABLED = _load_hot_reload_setting()

# 缓存配置
_config_cache = {
    "list": [],
    "mtime": 0,
    "path": ""
}

def _get_configs():
    path = get_latest_config_path()
    
    # 如果没启用热重载且已经加载过配置，直接返回缓存
    if not HOT_RELOAD_ENABLED and _config_cache["list"] and path == _config_cache["path"]:
        return _config_cache["list"]

    try:
        mtime = os.path.getmtime(path)
        if path != _config_cache["path"] or mtime > _config_cache["mtime"]:
            with open(path, 'r', encoding='utf-8') as f:
                _config_cache["list"] = json.load(f)
            _config_cache["mtime"] = mtime
            _config_cache["path"] = path
    except Exception as e:
        print(f"Error loading config: {e}")
        if not _config_cache["list"]:
            return []
    return _config_cache["list"]

# FOV 缩放常量：tan(120/2) / tan(72/2)
FOV_SCALE_120_72 = math.tan(math.radians(120 / 2)) / math.tan(math.radians(72 / 2))

# 计算余弦相似度
def calculate_cosine_similarity(v1, v2):
    # 计算两个向量的点积
    dot_product = np.dot(v1, v2)

    # 计算两个向量的长度
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)

    # 防止除以零（如果向量是零向量）
    if norm_v1 == 0 or norm_v2 == 0:
        return 0

    # 计算余弦相似度
    cosine_similarity = dot_product / (norm_v1 * norm_v2)

    return cosine_similarity


def posedict2state(keypoints, current_camera="72camera"):
    states = []
    config_list = _get_configs()

    for pose_template in config_list:
        if pose_template.get("inner_flag", False):
            continue
        if not pose_template.get("enable", True):
            continue
        pose_name = pose_template["name"]
        pose_base = pose_template["basekeypoints"]
        pose_index = pose_template["index"]
        pose_list = pose_template["list_corekeypoints"]
        pose_value_dict = pose_template["value_dict"]
        
        # 动作录制时的相机类型，默认为 72camera
        recorded_camera = pose_template.get("camera_type", "72camera")

        base_coordinates = keypoints[pose_base]
        v_template = []
        v_keypoints = []
        
        # 确定当前的缩放比例
        scale_x = 1.0
        if current_camera != recorded_camera:
            if current_camera == "120width_camera" and recorded_camera == "72camera":
                scale_x = FOV_SCALE_120_72
            elif current_camera == "72camera" and recorded_camera == "120width_camera":
                scale_x = 1.0 / FOV_SCALE_120_72

        for key in pose_list:
            v_template.extend(pose_value_dict[key])
            core_coordinates = keypoints[key] - base_coordinates
            
            # 仅在相机类型不一致时进行横向偏移缩放
            if scale_x != 1.0:
                core_coordinates[0] *= scale_x
                
            v_keypoints.extend(core_coordinates.tolist())

        # 计算向量夹角
        similarity = calculate_cosine_similarity(v_template, v_keypoints)

        threshold = pose_template.get("similarity_threshold", 0.95)
        if similarity >= threshold:
            states.append({'index': pose_index, 'name': pose_name})


    # 硬代码检测弯腰动作（仅当LeftLean且RightLean的inner_flag为True且启用时激活）
    has_left_lean = any(p.get("name") == "LeftLean" and p.get("inner_flag", False) and p.get("enable", True) for p in config_list)
    has_right_lean = any(p.get("name") == "RightLean" and p.get("inner_flag", False) and p.get("enable", True) for p in config_list)
    
    if has_left_lean and has_right_lean:
        mid_shoulder = (keypoints['left_shoulder'] + keypoints['right_shoulder']) / 2
        mid_hip = (keypoints['left_hip'] + keypoints['right_hip']) / 2
        vec = mid_shoulder - mid_hip
        angle = np.arctan2(vec[1], vec[0]) * 180 / np.pi
        # 计算相对于垂直线的倾斜角度
        vertical_angle = -90  # 垂直向下
        tilt_angle = abs(angle - vertical_angle)
        if tilt_angle > 10:  # 如果倾斜角度大于10度，认为是倾斜/弯腰
            if vec[0] < 0 and has_right_lean:
                states.append({'index': 14, 'name': 'RightLean'})
            elif vec[0] > 0 and has_left_lean:
                states.append({'index': 13, 'name': 'LeftLean'})

    # 检测转身动作（LeftTurn和RightTurn）
    has_left_turn = any(p.get("name") == "LeftTurn" and p.get("inner_flag", False) and p.get("enable", True) for p in config_list)
    has_right_turn = any(p.get("name") == "RightTurn" and p.get("inner_flag", False) and p.get("enable", True) for p in config_list)
    
    if has_left_turn or has_right_turn:
        try:
            # 计算双眼中点
            mid_eyes = (keypoints['left_eye'] + keypoints['right_eye']) / 2
            
            # 计算肩膀中点
            mid_shoulders = (keypoints['left_shoulder'] + keypoints['right_shoulder']) / 2
            
            # 计算胯部中点
            mid_hips = (keypoints['left_hip'] + keypoints['right_hip']) / 2
            
            # 向量1：双眼中点到肩膀中点的向量
            vector1 = mid_shoulders - mid_eyes
            
            # 向量2：肩膀中点到胯部中点的向量
            vector2 = mid_hips - mid_shoulders
            
            # 计算两个向量的夹角（使用atan2计算角度）
            angle1 = np.arctan2(vector1[1], vector1[0])
            angle2 = np.arctan2(vector2[1], vector2[0])
            
            # 计算夹角差（弧度）
            angle_diff = angle2 - angle1
            
            # 将角度差标准化到 [-pi, pi] 范围
            angle_diff = (angle_diff + np.pi) % (2 * np.pi) - np.pi
            
            # 转换为度数
            angle_diff_deg = angle_diff * 180 / np.pi
            
            # 根据夹角偏向判断转身方向
            # 如果夹角为正（顺时针），认为是右转
            # 如果夹角为负（逆时针），认为是左转
            turn_threshold = 15  # 转身角度阈值（度）
            
            if angle_diff_deg > turn_threshold and has_right_turn:
                states.append({'index': 25, 'name': 'RightTurn'})
            elif angle_diff_deg < -turn_threshold and has_left_turn:
                states.append({'index': 24, 'name': 'LeftTurn'})
                
        except KeyError as e:
            # 如果缺少关键点，跳过转身检测
            pass

    return states