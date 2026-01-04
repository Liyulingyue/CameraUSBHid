#!/usr/bin/env python

# Copyright (c) 2024, WuChao D-Robotics.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# 注意: 此程序在RDK板端端运行
# Attention: This program runs on RDK board.

import os
import cv2
import numpy as np

# scipy
try:
    from scipy.special import softmax
except:
    print("scipy is  not installed, installing.")
    os.system("pip install scipy")
    from scipy.special import softmax

# hobot_dnn
try:
    try:
        from hobot_dnn import pyeasy_dnn as dnn  # BSP Python API
    except:
        from hobot_dnn_rdkx5 import pyeasy_dnn as dnn  # BSP Python API from PyPI
except:
    print("pip install hobot-dnn-rdkx5")
    from hobot_dnn_rdkx5 import pyeasy_dnn as dnn

from time import time
import logging

# 日志模块配置
# logging configs
logging.basicConfig(
    level=logging.INFO,
    format='[%(name)s] [%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S')
logger = logging.getLogger("RDK_YOLO")

class Ultralytics_YOLO_Pose_Bayese_YUV420SP():
    def __init__(self, model_path, classes_num, nms_thres, score_thres, reg, strides, nkpt):
        # 加载BPU的bin模型, 打印相关参数
        # Load the quantized *.bin model and print its parameters
        try:
            begin_time = time()
            self.quantize_model = dnn.load(model_path)
            logger.debug("\033[1;31m" + "Load D-Robotics Quantize model time = %.2f ms"%(1000*(time() - begin_time)) + "\033[0m")
        except Exception as e:
            logger.error("❌ Failed to load model file: %s"%(model_path))
            logger.error("You can download the model file from the following docs: ./models/download.md") 
            logger.error(e)
            raise e

        logger.info("\033[1;32m" + "-> input tensors" + "\033[0m")
        for i, quantize_input in enumerate(self.quantize_model[0].inputs):
            logger.info(f"intput[{i}], name={quantize_input.name}, type={quantize_input.properties.dtype}, shape={quantize_input.properties.shape}")

        logger.info("\033[1;32m" + "-> output tensors" + "\033[0m")
        for i, quantize_input in enumerate(self.quantize_model[0].outputs):
            logger.info(f"output[{i}], name={quantize_input.name}, type={quantize_input.properties.dtype}, shape={quantize_input.properties.shape}")

        # init
        self.REG = reg
        self.CLASSES_NUM = classes_num
        self.SCORE_THRESHOLD = score_thres
        self.NMS_THRESHOLD = nms_thres
        self.CONF_THRES_RAW = -np.log(1/self.SCORE_THRESHOLD - 1)
        self.input_H, self.input_W = self.quantize_model[0].inputs[0].properties.shape[2:4]
        self.strides = strides
        self.nkpt = nkpt
        logger.info(f"{self.REG = }, {self.CLASSES_NUM = }")
        logger.info("SCORE_THRESHOLD  = %.2f, NMS_THRESHOLD = %.2f"%(self.SCORE_THRESHOLD, self.NMS_THRESHOLD))
        logger.info("CONF_THRES_RAW = %.2f"%self.CONF_THRES_RAW)
        logger.info(f"{self.input_H = }, {self.input_W = }")
        logger.info(f"{self.strides = }")
        logger.info(f"{self.nkpt = }")

        # DFL求期望的系数, 只需要生成一次
        # DFL calculates the expected coefficients, which only needs to be generated once.
        self.weights_static = np.array([i for i in range(reg)]).astype(np.float32)[np.newaxis, np.newaxis, :]
        logger.info(f"{self.weights_static.shape = }")

        # anchors, 只需要生成一次
        self.grids = []
        for stride in self.strides:
            assert self.input_H % stride == 0, f"{stride=}, {self.input_H=}: input_H % stride != 0"
            assert self.input_W % stride == 0, f"{stride=}, {self.input_W=}: input_W % stride != 0"
            grid_H, grid_W = self.input_H // stride, self.input_W // stride
            self.grids.append(np.stack([np.tile(np.linspace(0.5, grid_H-0.5, grid_H), reps=grid_H), 
                            np.repeat(np.arange(0.5, grid_W+0.5, 1), grid_W)], axis=0).transpose(1,0))
            logger.info(f"{self.grids[-1].shape = }")

    def preprocess_yuv420sp(self, img):
        RESIZE_TYPE = 0
        LETTERBOX_TYPE = 1
        PREPROCESS_TYPE = LETTERBOX_TYPE
        logger.info(f"PREPROCESS_TYPE = {PREPROCESS_TYPE}")

        begin_time = time()
        self.img_h, self.img_w = img.shape[0:2]
        if PREPROCESS_TYPE == RESIZE_TYPE:
            # 利用resize的方式进行前处理, 准备nv12的输入数据
            begin_time = time()
            input_tensor = cv2.resize(img, (self.input_W, self.input_H), interpolation=cv2.INTER_NEAREST) # 利用resize重新开辟内存节约一次
            input_tensor = self.bgr2nv12(input_tensor)
            self.y_scale = 1.0 * self.input_H / self.img_h
            self.x_scale = 1.0 * self.input_W / self.img_w
            self.y_shift = 0
            self.x_shift = 0
            logger.info("\033[1;31m" + f"pre process(resize) time = {1000*(time() - begin_time):.2f} ms" + "\033[0m")
        elif PREPROCESS_TYPE == LETTERBOX_TYPE:
            # 利用 letter box 的方式进行前处理, 准备nv12的输入数据
            begin_time = time()
            self.x_scale = min(1.0 * self.input_H / self.img_h, 1.0 * self.input_W / self.img_w)
            self.y_scale = self.x_scale
            
            if self.x_scale <= 0 or self.y_scale <= 0:
                raise ValueError("Invalid scale")
            
            resized_h, resized_w = int(self.img_h * self.y_scale), int(self.img_w * self.x_scale)
            resized_img = cv2.resize(img, (resized_w, resized_h), interpolation=cv2.INTER_NEAREST)
            
            # letter box
            self.y_shift = (self.input_H - resized_h) // 2
            self.x_shift = (self.input_W - resized_w) // 2
            
            canvas = np.full((self.input_H, self.input_W, 3), 114, dtype=np.uint8)
            canvas[self.y_shift:self.y_shift + resized_h, self.x_shift:self.x_shift + resized_w, :] = resized_img
            
            input_tensor = self.bgr2nv12(canvas)
            logger.info("\033[1;31m" + f"pre process(letter box) time = {1000*(time() - begin_time):.2f} ms" + "\033[0m")
            logger.debug("\033[1;31m" + f"pre process time = {1000*(time() - begin_time):.2f} ms" + "\033[0m")
            logger.info(f"y_scale = {self.y_scale:.2f}, x_scale = {self.x_scale:.2f}")
            logger.info(f"y_shift = {self.y_shift:.2f}, x_shift = {self.x_shift:.2f}")

        return input_tensor

    def bgr2nv12(self, bgr_img):
        """
        Convert a BGR image to the NV12 format.

        NV12 is a common video encoding format where the Y component (luminance) is full resolution,
        and the UV components (chrominance) are half-resolution and interleaved. This function first
        converts the BGR image to YUV 4:2:0 planar format, then rearranges the UV components to fit
        the NV12 format.

        Parameters:
        bgr_img (np.ndarray): The input BGR image array.

        Returns:
        np.ndarray: The converted NV12 format image array.
        """
        begin_time = time()
        height, width = bgr_img.shape[0], bgr_img.shape[1]
        area = height * width
        yuv420p = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2YUV_I420).reshape((area * 3 // 2,))
        y = yuv420p[:area]
        uv_planar = yuv420p[area:].reshape((2, area // 4))
        uv_packed = uv_planar.transpose((1, 0)).reshape((area // 2,))
        nv12 = np.zeros_like(yuv420p)
        nv12[:height * width] = y
        nv12[height * width:] = uv_packed

        logger.debug("\033[1;31m" + f"bgr8 to nv12 time = {1000*(time() - begin_time):.2f} ms" + "\033[0m")
        return nv12

    def forward(self, input_tensor):
        begin_time = time()
        quantize_outputs = self.quantize_model[0].forward(input_tensor)
        logger.debug("\033[1;31m" + f"forward time = {1000*(time() - begin_time):.2f} ms" + "\033[0m")
        return quantize_outputs

    def c2numpy(self, outputs):
        begin_time = time()
        outputs = [dnnTensor.buffer for dnnTensor in outputs]
        logger.debug("\033[1;31m" + f"c to numpy time = {1000*(time() - begin_time):.2f} ms" + "\033[0m")
        return outputs

    def postProcess(self, outputs):
        begin_time = time()
        # 解析输出
        s_cls = outputs[0].reshape(-1, self.CLASSES_NUM)
        s_bbox = outputs[1].reshape(-1, 64)
        s_kpt = outputs[2].reshape(-1, 51)
        m_cls = outputs[3].reshape(-1, self.CLASSES_NUM)
        m_bbox = outputs[4].reshape(-1, 64)
        m_kpt = outputs[5].reshape(-1, 51)
        l_cls = outputs[6].reshape(-1, self.CLASSES_NUM)
        l_bbox = outputs[7].reshape(-1, 64)
        l_kpt = outputs[8].reshape(-1, 51)

        # 筛选有效检测
        s_valid = s_cls.max(axis=1) >= self.CONF_THRES_RAW
        m_valid = m_cls.max(axis=1) >= self.CONF_THRES_RAW
        l_valid = l_cls.max(axis=1) >= self.CONF_THRES_RAW

        s_cls = s_cls[s_valid]
        s_bbox = s_bbox[s_valid]
        s_kpt = s_kpt[s_valid]
        m_cls = m_cls[m_valid]
        m_bbox = m_bbox[m_valid]
        m_kpt = m_kpt[m_valid]
        l_cls = l_cls[l_valid]
        l_bbox = l_bbox[l_valid]
        l_kpt = l_kpt[l_valid]

        # 如果没有检测到，返回空
        if len(s_cls) == 0 and len(m_cls) == 0 and len(l_cls) == 0:
            return []

        # sigmoid
        s_cls = 1 / (1 + np.exp(-s_cls))
        m_cls = 1 / (1 + np.exp(-m_cls))
        l_cls = 1 / (1 + np.exp(-l_cls))

        # DFL
        s_bbox = s_bbox.astype(np.float32) if len(s_bbox) > 0 else np.empty((0, 64))
        m_bbox = m_bbox.astype(np.float32) if len(m_bbox) > 0 else np.empty((0, 64))
        l_bbox = l_bbox.astype(np.float32) if len(l_bbox) > 0 else np.empty((0, 64))

        s_ltrb = np.sum(softmax(s_bbox.reshape(-1, 4, self.REG), axis=2) * self.weights_static, axis=2) if len(s_bbox) > 0 else np.empty((0, 4))
        m_ltrb = np.sum(softmax(m_bbox.reshape(-1, 4, self.REG), axis=2) * self.weights_static, axis=2) if len(m_bbox) > 0 else np.empty((0, 4))
        l_ltrb = np.sum(softmax(l_bbox.reshape(-1, 4, self.REG), axis=2) * self.weights_static, axis=2) if len(l_bbox) > 0 else np.empty((0, 4))

        s_grid = self.grids[0][s_valid]
        m_grid = self.grids[1][m_valid]
        l_grid = self.grids[2][l_valid]

        s_x1y1 = s_grid - s_ltrb[:, :2] if len(s_ltrb) > 0 else np.empty((0, 2))
        s_x2y2 = s_grid + s_ltrb[:, 2:] if len(s_ltrb) > 0 else np.empty((0, 2))
        s_bbox = np.hstack([s_x1y1, s_x2y2]) * 8 if len(s_x1y1) > 0 else np.empty((0, 4))

        m_x1y1 = m_grid - m_ltrb[:, :2] if len(m_ltrb) > 0 else np.empty((0, 2))
        m_x2y2 = m_grid + m_ltrb[:, 2:] if len(m_ltrb) > 0 else np.empty((0, 2))
        m_bbox = np.hstack([m_x1y1, m_x2y2]) * 16 if len(m_x1y1) > 0 else np.empty((0, 4))

        l_x1y1 = l_grid - l_ltrb[:, :2] if len(l_ltrb) > 0 else np.empty((0, 2))
        l_x2y2 = l_grid + l_ltrb[:, 2:] if len(l_ltrb) > 0 else np.empty((0, 2))
        l_bbox = np.hstack([l_x1y1, l_x2y2]) * 32 if len(l_x1y1) > 0 else np.empty((0, 4))

        # keypoints
        s_kpt = s_kpt.astype(np.float32) if len(s_kpt) > 0 else np.empty((0, 51))
        m_kpt = m_kpt.astype(np.float32) if len(m_kpt) > 0 else np.empty((0, 51))
        l_kpt = l_kpt.astype(np.float32) if len(l_kpt) > 0 else np.empty((0, 51))

        s_kpt = s_kpt.reshape(-1, self.nkpt, 3) if len(s_kpt) > 0 else np.empty((0, self.nkpt, 3))
        s_kpt_xy = (s_kpt[:, :, :2] * 2 + s_grid[:, np.newaxis, :] - 0.5) * 8 if len(s_kpt) > 0 else np.empty((0, self.nkpt, 2))
        s_kpt_conf = 1 / (1 + np.exp(-s_kpt[:, :, 2:])) if len(s_kpt) > 0 else np.empty((0, self.nkpt, 1))

        m_kpt = m_kpt.reshape(-1, self.nkpt, 3) if len(m_kpt) > 0 else np.empty((0, self.nkpt, 3))
        m_kpt_xy = (m_kpt[:, :, :2] * 2 + m_grid[:, np.newaxis, :] - 0.5) * 16 if len(m_kpt) > 0 else np.empty((0, self.nkpt, 2))
        m_kpt_conf = 1 / (1 + np.exp(-m_kpt[:, :, 2:])) if len(m_kpt) > 0 else np.empty((0, self.nkpt, 1))

        l_kpt = l_kpt.reshape(-1, self.nkpt, 3) if len(l_kpt) > 0 else np.empty((0, self.nkpt, 3))
        l_kpt_xy = (l_kpt[:, :, :2] * 2 + l_grid[:, np.newaxis, :] - 0.5) * 32 if len(l_kpt) > 0 else np.empty((0, self.nkpt, 2))
        l_kpt_conf = 1 / (1 + np.exp(-l_kpt[:, :, 2:])) if len(l_kpt) > 0 else np.empty((0, self.nkpt, 1))

        # concat
        bboxes = np.concatenate([s_bbox, m_bbox, l_bbox], axis=0)
        scores = np.concatenate([s_cls.max(axis=1), m_cls.max(axis=1), l_cls.max(axis=1)], axis=0)
        classes = np.concatenate([s_cls.argmax(axis=1), m_cls.argmax(axis=1), l_cls.argmax(axis=1)], axis=0)
        kpts_xy = np.concatenate([s_kpt_xy, m_kpt_xy, l_kpt_xy], axis=0)
        kpts_conf = np.concatenate([s_kpt_conf, m_kpt_conf, l_kpt_conf], axis=0)

        # nms
        indices = cv2.dnn.NMSBoxes(bboxes, scores, self.SCORE_THRESHOLD, self.NMS_THRESHOLD)

        # scale back
        bboxes = bboxes[indices]
        bboxes[:, [0, 2]] = (bboxes[:, [0, 2]] - self.x_shift) / self.x_scale
        bboxes[:, [1, 3]] = (bboxes[:, [1, 3]] - self.y_shift) / self.y_scale
        bboxes = bboxes.astype(np.int32)

        kpts_xy = kpts_xy[indices]
        kpts_xy[:, :, 0] = (kpts_xy[:, :, 0] - self.x_shift) / self.x_scale
        kpts_xy[:, :, 1] = (kpts_xy[:, :, 1] - self.y_shift) / self.y_scale

        kpts_conf = kpts_conf[indices]

        results = []
        for i in range(len(bboxes)):
            x1, y1, x2, y2 = bboxes[i]
            cls = classes[indices[i]]
            score = scores[indices[i]]
            kpts = np.hstack([kpts_xy[i], kpts_conf[i]])
            results.append((cls, score, x1, y1, x2, y2, kpts))

        logger.debug("\033[1;31m" + f"Post Process time = {1000*(time() - begin_time):.2f} ms" + "\033[0m")
        return results

class YOLO11PoseEstimator:
    """
    YOLO11 Pose Estimator 类，用于封装YOLO11-Pose模型的加载、推理和绘制功能。
    """
    def __init__(self, model_path='model/yolo11n_pose_bayese_640x640_nv12.bin', score_thres=0.25, nms_thres=0.7, kpt_conf_thres=0.5):
        """
        初始化Estimator。

        Args:
            model_path (str): 模型文件路径。
            score_thres (float): 检测置信度阈值。
            nms_thres (float): NMS阈值。
            kpt_conf_thres (float): 关键点置信度阈值。
        """
        self.model_path = model_path
        self.score_thres = score_thres
        self.nms_thres = nms_thres
        self.kpt_conf_thres = kpt_conf_thres
        self.model = None  # 模型将在 load() 中加载

    def load(self):
        """
        加载模型。如果模型不存在，则下载。
        """
        if self.model is not None:
            logger.info("Model already loaded.")
            return

        load_start = time()
        # 检查模型是否存在，如果不存在则下载
        if not os.path.exists(self.model_path):
            error_msg = (
                f"Model file not found: {self.model_path}.\n"
                "Please download it from: https://archive.d-robotics.cc/downloads/rdk_model_zoo/rdk_x5/ultralytics_YOLO/yolo11n_pose_bayese_640x640_nv12.bin\n"
                f"And place it at: {self.model_path}\n"
                "You can use wget or curl to download, e.g., wget -O {self.model_path} <url>"
            )
            raise FileNotFoundError(error_msg)

        # 加载模型
        self.model = Ultralytics_YOLO_Pose_Bayese_YUV420SP(
            model_path=self.model_path,
            classes_num=1,
            nms_thres=self.nms_thres,
            score_thres=self.score_thres,
            reg=16,
            strides=[8, 16, 32],
            nkpt=17
        )
        load_time = time() - load_start
        logger.info(f"Model loaded in {load_time:.2f} seconds.")

    def infer(self, image):
        """
        进行推理。

        Args:
            image (str or np.ndarray): 输入图像路径或图像对象。

        Returns:
            dict: 包含检测结果的字典。
                - 'num_detections': int, 检测到的对象数量。
                - 'detections': list of dicts, 每个检测包含 'bbox', 'score', 'keypoints'。
        """
        if self.model is None:
            self.load()

        # 读图或使用传入的图像对象
        if isinstance(image, str):
            img = cv2.imread(image)
            if img is None:
                raise ValueError(f"无法读取图像: {image}")
        elif isinstance(image, np.ndarray):
            img = image
        else:
            raise ValueError("image 参数必须是图像路径 (str) 或图像对象 (np.ndarray)")

        # 准备输入数据
        input_tensor = self.model.preprocess_yuv420sp(img)

        # 推理
        outputs = self.model.c2numpy(self.model.forward(input_tensor))

        # 后处理
        results = self.model.postProcess(outputs)

        # 组织结果
        detections = []
        for cls, score, x1, y1, x2, y2, kpts in results:
            keypoints = []
            for j in range(17):
                x, y, conf = kpts[j]
                if conf < self.kpt_conf_thres:
                    keypoints.append([0, 0, 0])
                else:
                    keypoints.append([float(x), float(y), float(conf)])
            detections.append({
                'bbox': [x1, y1, x2, y2],
                'score': float(score),
                'keypoints': keypoints
            })

        return {
            'num_detections': len(detections),
            'detections': detections
        }

    def draw_results(self, image, results):
        """
        在图像上绘制检测结果。

        Args:
            image (np.ndarray): 输入图像。
            results (dict): 推理结果。

        Returns:
            np.ndarray: 绘制后的图像。
        """
        img = image.copy()
        for det in results['detections']:
            x1, y1, x2, y2 = det['bbox']
            score = det['score']
            keypoints = det['keypoints']

            # 绘制边界框
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img, f"Person: {score:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # 绘制关键点
            for j, (x, y, conf) in enumerate(keypoints):
                if conf > 0:
                    cv2.circle(img, (int(x), int(y)), 5, (0, 0, 255), -1)
                    cv2.putText(img, str(j), (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

        return img

    def close(self):
        """
        释放资源（如果需要）。
        """
        # 如果有释放方法，可以在这里调用
        pass

if __name__ == "__main__":
    # 示例使用
    # 注意: 请确保模型文件已下载到指定路径，否则 load() 会抛出异常
    estimator = YOLO11PoseEstimator(model_path="model/yolo11s_pose_bayese_640x640_nv12.bin")
    
    # 加载模型
    estimator.load()
    
    # 方式1: 使用图像路径
    infer_start = time()
    results = estimator.infer('test2.png')
    infer_time = time() - infer_start
    fps = 1.0 / infer_time if infer_time > 0 else 0
    print(f"推理时间 (路径方式): {infer_time:.2f} 秒")
    print(f"FPS (路径方式): {fps:.2f}")
    print("检测结果 (路径方式):")
    print(f"检测到 {results['num_detections']} 个对象")
    
    # 方式2: 使用图像对象
    img = cv2.imread('test2.png')
    infer_start = time()
    results2 = estimator.infer(img)
    infer_time = time() - infer_start
    fps = 1.0 / infer_time if infer_time > 0 else 0
    print(f"推理时间 (图像对象方式): {infer_time:.2f} 秒")
    print(f"FPS (图像对象方式): {fps:.2f}")
    print("检测结果 (图像对象方式):")
    print(f"检测到 {results2['num_detections']} 个对象")
    
    # 绘制
    drawn_img = estimator.draw_results(img, results)
    cv2.imwrite('result.png', drawn_img)
    print("结果已保存到 result.png")
    
    # 释放
    estimator.close()