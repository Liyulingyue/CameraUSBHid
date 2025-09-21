from .decoder import OpenPoseDecoder
from .utils import create_model, model_predict, draw_poses, body_mapper

class HumanPoseEstimator():
    def __init__(self, model_path="Source/Models/human-pose-estimation-0001/FP16-INT8/human-pose-estimation-0001.xml", device="CPU"):
        self.model_infor = create_model(model_path, device)
        self.decoder = OpenPoseDecoder()

    def infer(self, image, is_draw=False):
        result = model_predict(image, self.model_infor, self.decoder)
        draw_img = draw_poses(image, result, point_score_threshold=0.1) if is_draw else image
        return result, draw_img

    def pose2dict(self, poses):
        if len(poses) == 0:
            pose_dict = {}
        else:
            pose_dict = {key: poses[0, body_mapper[key], :2] for key in body_mapper.keys()}
        return pose_dict
