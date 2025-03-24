import cv2

from Tools.ov.decoder import OpenPoseDecoder
from Tools.ov.utils import create_model, model_predict, draw_poses

if __name__ == '__main__':
    decoder = OpenPoseDecoder()
    model_infor = create_model("Models/human-pose-estimation-0001/FP16-INT8/human-pose-estimation-0001.xml", "CPU")
    frame = cv2.imread('example.jpg')
    poses = model_predict(frame, model_infor, decoder)
    # print(poses)
    drawed_frame = draw_poses(frame, poses, point_score_threshold=0.1)
    # cv2.imshow('image', drawed_frame)
    # cv2.waitKey(0)

    # 测试速率，进行1000次预测，记录时间，取均值，输出FPS
    import time
    start_time = time.time()
    test_range = 10000
    for i in range(test_range):
        poses = model_predict(frame, model_infor, decoder)
    end_time = time.time()
    print("fps is:",1 / ((end_time - start_time) / test_range))

