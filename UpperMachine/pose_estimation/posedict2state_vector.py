import numpy as np
import json

config_list = json.load(open("Source/configs.json"))

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


def posedict2state(keypoints):
    states = []

    for pose_template in config_list:
        if pose_template.get("inner_flag", False):
            continue
        pose_name = pose_template["name"]
        pose_base = pose_template["basekeypoints"]
        pose_index = pose_template["index"]
        pose_list = pose_template["list_corekeypoints"]
        pose_value_dict = pose_template["value_dict"]

        base_coordinates = keypoints[pose_base]
        v_template = []
        v_keypoints = []
        for key in pose_list:
            v_template.extend(pose_value_dict[key])
            core_coordinates = keypoints[key] - base_coordinates
            v_keypoints.extend(core_coordinates.tolist())

        # 计算向量夹角
        similarity = calculate_cosine_similarity(v_template, v_keypoints)

        threshold = pose_template.get("similarity_threshold", 0.95)
        if similarity >= threshold:
            states.append({'index': pose_index, 'name': pose_name})


    # 硬代码检测弯腰动作（仅当LeftLean且RightLean的inner_flag为True时激活）
    has_left_lean = any(p.get("name") == "LeftLean" and p.get("inner_flag", False) for p in config_list)
    has_right_lean = any(p.get("name") == "RightLean" and p.get("inner_flag", False) for p in config_list)
    
    if has_left_lean and has_right_lean:
        mid_shoulder = (keypoints['left_shoulder'] + keypoints['right_shoulder']) / 2
        mid_hip = (keypoints['left_hip'] + keypoints['right_hip']) / 2
        vec = mid_shoulder - mid_hip
        angle = np.arctan2(vec[1], vec[0]) * 180 / np.pi
        # 计算相对于垂直线的倾斜角度
        vertical_angle = -90  # 垂直向下
        tilt_angle = abs(angle - vertical_angle)
        if tilt_angle > 10:  # 如果倾斜角度大于10度，认为是弯腰
            if vec[0] < 0 and has_left_lean:
                states.append({'index': 13, 'name': 'LeftLean'})
            elif vec[0] > 0 and has_right_lean:
                states.append({'index': 14, 'name': 'RightLean'})

    return states