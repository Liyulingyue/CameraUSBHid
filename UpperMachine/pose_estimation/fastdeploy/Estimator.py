import os.path

import fastdeploy
import numpy as np

from .utils import body_mapper, draw_poses


class HumanPoseEstimator():
    def __init__(self, model_path="Source/Models/tinypose_128x96", device="CPU"):
        self.model = fastdeploy.vision.keypointdetection.PPTinyPose(
            os.path.join(model_path, "model.pdmodel"),
            os.path.join(model_path, "model.pdiparams"),
            os.path.join(model_path, "infer_cfg.yml"))

    def infer(self, image, is_draw=False):
        result = self.model.predict(image)
        keypoints = np.array(result.keypoints).reshape(-1, 17, 2)
        scores = np.array(result.scores).reshape(-1, 17, 1)
        result = np.concatenate((keypoints, scores), axis=2)

        draw_img = draw_poses(image, result, point_score_threshold=0.1) if is_draw else image
        return result, draw_img

    def pose2dict(self, poses):
        if len(poses) == 0:
            pose_dict = {}
        else:
            pose_dict = {key: poses[0, body_mapper[key], :2] for key in body_mapper.keys()}
        return pose_dict
