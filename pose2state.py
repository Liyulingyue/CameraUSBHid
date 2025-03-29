import numpy as np


def calculate_distance(point1, point2, type='euclidean'):
    distance = 0
    if type == 'euclidean':
        distance = np.linalg.norm(np.array(point1) - np.array(point2))
    elif type == "x":
        distance = abs(point1[0] - point2[0])
    elif type == "y":
        distance = abs(point1[1] - point2[1])
    else: # default
        distance = np.linalg.norm(np.array(point1) - np.array(point2))
    return distance


def judge_pose(keypoints):
    states = []

    # Extract relevant points
    nose = keypoints['nose']
    right_shoulder = keypoints['right_shoulder']
    left_shoulder = keypoints['left_shoulder']
    right_wrist = keypoints['right_wrist']
    left_wrist = keypoints['left_wrist']
    right_elbow = keypoints['right_elbow']
    left_elbow = keypoints['left_elbow']
    right_hip = keypoints['right_hip']  # Using hip as a reference for waist-level叉腰动作
    left_hip = keypoints['left_hip']

    # Calculate distance between shoulders
    shoulder_distance = calculate_distance(right_shoulder, left_shoulder)

    # 0. 双手交叉 双手在胸前合上 效果不好
    if (calculate_distance(right_wrist, right_shoulder, "y") > 0.7 * calculate_distance(right_wrist, right_hip, "y") and
            calculate_distance(right_wrist, right_hip, "y") > 0.7 * calculate_distance(right_wrist, right_shoulder, "y") and
            calculate_distance(left_wrist, left_shoulder, "y") > 0.7 * calculate_distance(left_wrist, left_hip, "y") and
            calculate_distance(left_wrist, left_hip, "y") > 0.7 * calculate_distance(left_wrist, left_shoulder, "y") and
            calculate_distance(right_wrist, left_wrist) < 0.3 * shoulder_distance):
        states.append("双手交叉")

    # 1. 右手摸左肩膀
    if calculate_distance(right_wrist, left_shoulder) < 0.3 * shoulder_distance:  # 20% of shoulder distance as threshold
        states.append("右手摸左肩膀")

    # 2. 左手摸右肩膀
    if calculate_distance(left_wrist, right_shoulder) < 0.3 * shoulder_distance:
        states.append("左手摸右肩膀")

    # 3. 右手叉腰 右手在肩膀和胯部的中间位置，且右手肘和肩膀的距离约等于两肩距离的70%以上
    if (calculate_distance(right_wrist, right_shoulder, "y") > 0.7 * calculate_distance(right_wrist, right_hip, "y") and
            calculate_distance(right_wrist, right_hip, "y") > 0.7 * calculate_distance(right_wrist, right_shoulder, "y") and
            calculate_distance(right_wrist, right_shoulder, "x") < 0.2 * shoulder_distance and
            calculate_distance(right_wrist, right_elbow) > 0.3 * shoulder_distance):
        states.append("右手叉腰")

    # 4. 左手叉腰
    if (calculate_distance(left_wrist, left_shoulder, "y") > 0.7 * calculate_distance(left_wrist, left_hip, "y") and
            calculate_distance(left_wrist, left_hip, "y") > 0.7 * calculate_distance(left_wrist, left_shoulder, "y") and
            calculate_distance(left_wrist, left_shoulder, "x") < 0.2 * shoulder_distance and
            calculate_distance(left_wrist, left_elbow) > 0.3 * shoulder_distance):
        states.append("左手叉腰")

    # 5. 右手举起
    if (right_wrist[1] < nose[1] and
            right_elbow[1] > nose[1]):
        states.append("右手举起")

    # 6. 左手举起
    if (left_wrist[1] < nose[1] and
            left_elbow[1] > nose[1]):
        states.append("左手举起")

    # 7. 右手向右平举
    if (calculate_distance(right_wrist, right_shoulder, "y") > 0.7 * calculate_distance(right_wrist, right_hip, "y") and
            calculate_distance(right_wrist, right_hip, "y") > 0.7 * calculate_distance(right_wrist, right_shoulder, "y") and
            calculate_distance(right_wrist, right_shoulder, "x") > 1 * shoulder_distance):
        states.append("右手平伸")

    # 8. 左手向左平举
    if (calculate_distance(left_wrist, left_shoulder, "y") > 0.7 * calculate_distance(left_wrist, left_hip, "y") and
            calculate_distance(left_wrist, left_hip, "y") > 0.7 * calculate_distance(left_wrist, left_shoulder, "y") and
            calculate_distance(left_wrist, left_shoulder, "x") > 1 * shoulder_distance):
        states.append("左手平伸")

    # 9. 右手V 右手和右肩的x轴距离大于两肩距离的70%，并且远离左键，且右手的高度和肩膀的y轴距离小于两肩距离的20%
    if (calculate_distance(right_wrist, right_shoulder, "x") > 0.7 * shoulder_distance and
            calculate_distance(right_wrist, left_shoulder, "x") > 1.5 * shoulder_distance and
            calculate_distance(right_wrist, right_shoulder, "y") < 0.2 * shoulder_distance):
        states.append("右手V")

    # 10. 左手V 左手和左肩的x轴距离大于两肩距离的70%，并且远离右键，且左手的高度和肩膀的y轴距离小于两肩距离的20%
    if (calculate_distance(left_wrist, left_shoulder, "x") > 0.7 * shoulder_distance and
            calculate_distance(left_wrist, right_shoulder, "x") > 1.5 * shoulder_distance and
            calculate_distance(left_wrist, left_shoulder, "y") < 0.2 * shoulder_distance):
        states.append("左手V")

    return states

if __name__ == "__main__":
    # Example usage
    keypoints_example = {
        'nose': np.array([314.53946, 168.0]),
        'right_eye': np.array([326.52194, 120.0]),
        'left_eye': np.array([296.5658, 136.0]),
        'right_ear': np.array([356.47806, 120.0]),
        'left_ear': np.array([284.58334, 152.0]),
        'right_shoulder': np.array([434.36404, 232.0]),
        'left_shoulder': np.array([284.58334, 280.0]),
        'right_elbow': np.array([470.3114, 376.0]),
        'left_elbow': np.array([236.6535, 376.0]),
        'right_wrist': np.array([410.3991, 440.0]),
        'left_wrist': np.array([242.64473, 520.0]),
        'right_hip': np.array([392.42545, 536.0]),
        'left_hip': np.array([320.5307, 520.0]),
        'right_knee': np.array([410.3991, 712.0]),
        'left_knee': np.array([302.557, 600.0]),
        'right_ankle': np.array([350.48685, 808.0]),
        'left_ankle': np.array([356.47806, 888.0])
    }

    print(judge_pose(keypoints_example))