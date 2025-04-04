import numpy as np
from numpy.lib.stride_tricks import as_strided
import cv2
colors = ((255, 0, 0), (255, 0, 255), (170, 0, 255), (255, 0, 85), (255, 0, 170), (85, 255, 0),
          (255, 170, 0), (0, 255, 0), (255, 255, 0), (0, 255, 85), (170, 255, 0), (0, 85, 255),
          (0, 255, 170), (0, 0, 255), (0, 255, 255), (85, 0, 255), (0, 170, 255))

default_skeleton = ((15, 13), (13, 11), (16, 14), (14, 12), (11, 12), (5, 11), (6, 12), (5, 6), (5, 7),
                    (6, 8), (7, 9), (8, 10), (1, 2), (0, 1), (0, 2), (1, 3), (2, 4), (3, 5), (4, 6))

body_mapper = {
    "nose": 0,
    "right_eye": 1,
    "left_eye": 2,
    "right_ear": 3,
    "left_ear": 4,
    "right_shoulder": 5,
    "left_shoulder": 6,
    "right_elbow": 7,
    "left_elbow": 8,
    "right_wrist": 9,
    "left_wrist": 10,
    "right_hip": 11,
    "left_hip": 12,
    "right_knee": 13,
    "left_knee": 14,
    "right_ankle": 15,
    "left_ankle": 16
}

def draw_poses(img, poses, point_score_threshold=0.5, skeleton=default_skeleton):
    if poses.size == 0:
        return img

    img_limbs = np.copy(img)
    for pose in poses:
        points = pose[:, :2].astype(np.int32)
        points_scores = pose[:, 2]
        # Draw joints.
        for i, (p, v) in enumerate(zip(points, points_scores)):
            if v > point_score_threshold:
                cv2.circle(img, tuple(p), 1, colors[i], 2)
                cv2.putText(img, str(i), tuple(p), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[i], 1)
        # Draw limbs.
        for i, j in skeleton:
            if points_scores[i] > point_score_threshold and points_scores[j] > point_score_threshold:
                cv2.line(img_limbs, tuple(points[i]), tuple(points[j]), color=colors[j], thickness=4)
    cv2.addWeighted(img, 0.4, img_limbs, 0.6, 0, dst=img)
    return img