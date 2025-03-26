import numpy as np


def calculate_distance(point1, point2):
    return np.linalg.norm(np.array(point1) - np.array(point2))


def judge_pose(keypoints):
    states = []

    # Extract relevant points
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

    # 1. 右手摸左肩膀
    if calculate_distance(right_wrist,
                          left_shoulder) < 0.2 * shoulder_distance:  # 20% of shoulder distance as threshold
        states.append("右手摸左肩膀")

    # 2. 左手摸右肩膀
    if calculate_distance(left_wrist, right_shoulder) < 0.2 * shoulder_distance:
        states.append("左手摸右肩膀")

    # 3. 双手抱胸
    if (calculate_distance(right_elbow, right_wrist) < 50 and
            calculate_distance(left_elbow, left_wrist) < 50):  # Arbitrary threshold for close
        states.append("双手抱胸")

    # 4. 右手叉腰 (Assume waist level is near hips)
    if calculate_distance(right_wrist, right_hip) < 50:  # Arbitrary threshold
        states.append("右手叉腰")

    # 5. 左手叉腰
    if calculate_distance(left_wrist, left_hip) < 50:
        states.append("左手叉腰")

    # 6. 右手摸右肩膀
    if calculate_distance(right_wrist, right_shoulder) < 0.2 * shoulder_distance:
        states.append("右手摸右肩膀")

    # 7. 左手摸左肩膀
    if calculate_distance(left_wrist, left_shoulder) < 0.2 * shoulder_distance:
        states.append("左手摸左肩膀")

    # 8. 右手举起 (Simplified condition: arm approximately horizontal)
    # Assume "举起" means the wrist is higher than the shoulder and elbow forms ~90 degrees with shoulder line
    right_arm_vector = np.array(right_wrist) - np.array(right_elbow)
    right_shoulder_to_elbow = np.array(right_elbow) - np.array(right_shoulder)
    if (right_wrist[1] < right_shoulder[1] and  # Wrist higher than shoulder vertically
            np.abs(np.dot(right_arm_vector, right_shoulder_to_elbow)) /
            (np.linalg.norm(right_arm_vector) * np.linalg.norm(
                right_shoulder_to_elbow)) < 0.707):  # Cosine of ~45 degrees for close-to-right-angle
        states.append("右手举起")

    # 9. 左手举起
    left_arm_vector = np.array(left_wrist) - np.array(left_elbow)
    left_shoulder_to_elbow = np.array(left_elbow) - np.array(left_shoulder)
    if (left_wrist[1] < left_shoulder[1] and
            np.abs(np.dot(left_arm_vector, left_shoulder_to_elbow)) /
            (np.linalg.norm(left_arm_vector) * np.linalg.norm(left_shoulder_to_elbow)) < 0.707):
        states.append("左手举起")

    # 10. 右手直举 (Simplified: arm straight up or down)
    if np.abs(right_wrist[0] - right_shoulder[0]) < 20:  # Minimal horizontal deviation
        states.append("右手直举")

    # 11. 左手直举
    if np.abs(left_wrist[0] - left_shoulder[0]) < 20:
        states.append("左手直举")

    return states


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