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


def posedict2state(keypoints, type="undebug"):
    states = []

    for pose_template in config_list:
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

        if (pose_index not in [3, 4]) and similarity >= 0.95:
            states.append(pose_index if type == "undebug" else pose_name)
        elif similarity >=0.975:
            states.append(pose_index if type == "undebug" else pose_name)


    return states