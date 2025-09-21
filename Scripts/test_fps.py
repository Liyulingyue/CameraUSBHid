import cv2

# from UpperMachine.ov.Estimator import HumanPoseEstimator
# model_path = "Source/Models/human-pose-estimation-0001/FP16-INT8/human-pose-estimation-0001.xml"
# device = "CPU"
# estimator = HumanPoseEstimator(model_path, device)

from UpperMachine.pose_estimation.fastdeploy.Estimator import HumanPoseEstimator
model_path = "Source/Models/tinypose_128x96"
device = "CPU"
estimator = HumanPoseEstimator(model_path, device)

if __name__ == '__main__':

    frame = cv2.imread('example.jpg')
    poses, drawed_frame = estimator.infer(frame, True)
    # print(poses)
    # cv2.imshow('image', drawed_frame)
    # cv2.waitKey(0)
    pose_dict = estimator.pose2dict(poses)
    print(pose_dict)

    # 测试速率，进行1000次预测，记录时间，取均值，输出FPS
    import time
    start_time = time.time()
    test_range = 10
    for i in range(test_range):
        poses, drawed_frame = estimator.infer(frame, False)
    end_time = time.time()
    print("fps is:",1 / ((end_time - start_time) / test_range))

