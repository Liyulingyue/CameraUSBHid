from libs.PipeLine import PipeLine, ScopedTiming
from libs.AIBase import AIBase
from libs.AI2D import Ai2d
import os
import ujson
from media.media import *
from time import *
import nncase_runtime as nn
import ulab.numpy as np
import time
import utime
import image
import random
import gc
import sys
import aidemo
import network
import socket


IF_SEND_COMMAND = True # 是否发送命令
DEBUG_FLAG = "undebug" # 调试模式，可选值："debug"、"undebug"
server_ip = '192.168.2.121'
port = 80
last_command = ""
WLAN_SSID = "****"
WLAN_PASSWORD = "****"


config_list = [
        {
            "name": "LeftHandOnHead",
            "index": 8,
            "basekeypoints": "left_shoulder",
            "list_corekeypoints": [
                "left_elbow",
                "left_wrist",
                "left_eye"
            ],
            "value_dict": {
                "left_elbow": [
                    -95.6089096069336,
                    -22.876571655273438
                ],
                "left_wrist": [
                    -6.1168212890625,
                    -107.35348510742188
                ],
                "left_eye": [
                    73.0457763671875,
                    -131.6073226928711
                ]
            }
        },
        {
            "name": "LeftHandOnHip",
            "index": 4,
            "basekeypoints": "left_shoulder",
            "list_corekeypoints": [
                "left_elbow",
                "left_wrist"
            ],
            "value_dict": {
                "left_elbow": [
                    -76.60369873046875,
                    93.453125
                ],
                "left_wrist": [
                    -4.2689208984375,
                    159.2177734375
                ]
            }
        },
        {
            "name": "LeftHandOnShoulder",
            "index": 12,
            "basekeypoints": "left_shoulder",
            "list_corekeypoints": [
                "left_elbow",
                "left_wrist",
                "right_shoulder"
            ],
            "value_dict": {
                "left_elbow": [
                    7.4216461181640625,
                    81.56442260742188
                ],
                "left_wrist": [
                    109.91059875488281,
                    -0.9780426025390625
                ],
                "right_shoulder": [
                    172.7346954345703,
                    -5.5809173583984375
                ]
            }
        },
        {
            "name": "LeftHandOut",
            "index": 10,
            "basekeypoints": "left_shoulder",
            "list_corekeypoints": [
                "left_elbow",
                "left_wrist"
            ],
            "value_dict": {
                "left_elbow": [
                    -64.655517578125,
                    117.84085083007812
                ],
                "left_wrist": [
                    -132.79608154296875,
                    54.8519287109375
                ]
            }
        },
        {
            "name": "LeftHandUp",
            "index": 6,
            "basekeypoints": "left_shoulder",
            "list_corekeypoints": [
                "left_elbow",
                "left_wrist"
            ],
            "value_dict": {
                "left_elbow": [
                    -76.25718688964844,
                    -93.91152954101562
                ],
                "left_wrist": [
                    -66.80403137207031,
                    -224.44114685058594
                ]
            }
        },
        {
            "name": "LeftV",
            "index": 2,
            "basekeypoints": "left_shoulder",
            "list_corekeypoints": [
                "left_elbow",
                "left_wrist"
            ],
            "value_dict": {
                "left_elbow": [
                    -76.67457580566406,
                    81.17578125
                ],
                "left_wrist": [
                    -157.1609649658203,
                    -39.96327209472656
                ]
            }
        },
        {
            "name": "RightHandOnHead",
            "index": 7,
            "basekeypoints": "right_shoulder",
            "list_corekeypoints": [
                "right_elbow",
                "right_wrist",
                "right_eye"
            ],
            "value_dict": {
                "right_elbow": [
                    83.32156372070312,
                    -85.59181213378906
                ],
                "right_wrist": [
                    -33.407562255859375,
                    -150.03038024902344
                ],
                "right_eye": [
                    -87.55984497070312,
                    -114.21543884277344
                ]
            }
        },
        {
            "name": "RightHandOnHip",
            "index": 3,
            "basekeypoints": "right_shoulder",
            "list_corekeypoints": [
                "right_elbow",
                "right_wrist"
            ],
            "value_dict": {
                "right_elbow": [
                    95.72293090820312,
                    82.81088256835938
                ],
                "right_wrist": [
                    31.795166015625,
                    177.29721069335938
                ]
            }
        },
        {
            "name": "RightHandOnShoulder",
            "index": 11,
            "basekeypoints": "right_shoulder",
            "list_corekeypoints": [
                "right_elbow",
                "right_wrist",
                "left_shoulder"
            ],
            "value_dict": {
                "right_elbow": [
                    6.30242919921875,
                    90.78425598144531
                ],
                "right_wrist": [
                    -111.33969116210938,
                    31.734481811523438
                ],
                "left_shoulder": [
                    -167.52532958984375,
                    24.355514526367188
                ]
            }
        },
        {
            "name": "RightHandOut",
            "index": 9,
            "basekeypoints": "right_shoulder",
            "list_corekeypoints": [
                "right_elbow",
                "right_wrist"
            ],
            "value_dict": {
                "right_elbow": [
                    69.11349487304688,
                    68.037841796875
                ],
                "right_wrist": [
                    161.825439453125,
                    71.52139282226562
                ]
            }
        },
        {
            "name": "RightHandUp",
            "index": 5,
            "basekeypoints": "right_shoulder",
            "list_corekeypoints": [
                "right_elbow",
                "right_wrist"
            ],
            "value_dict": {
                "right_elbow": [
                    80.53787231445312,
                    -99.63442993164062
                ],
                "right_wrist": [
                    66.98867797851562,
                    -219.03517150878906
                ]
            }
        },
        {
            "name": "RightV",
            "index": 1,
            "basekeypoints": "right_shoulder",
            "list_corekeypoints": [
                "right_elbow",
                "right_wrist"
            ],
            "value_dict": {
                "right_elbow": [
                    108.55154418945312,
                    55.9530029296875
                ],
                "right_wrist": [
                    177.73501586914062,
                    -42.712554931640625
                ]
            }
        }
    ]

words2bytes_dict = {
    's': 0x16,
    'w': 0x1A,
    'd': 0x07,
    'a': 0x04,
    'j': 0x0D,
    'k': 0x0E,
    'e': 0x08,
    'q': 0x14,
    'i': 0x0C,
    'o': 0x12,
    'n': 0x11,
    'm': 0x10,
}

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



def network_use_wlan(is_wlan=True):
    if is_wlan:
        sta=network.WLAN(0)
        sta.connect(WLAN_SSID, WLAN_PASSWORD)
        print(sta.status())
        while sta.ifconfig()[0] == '0.0.0.0':
            os.exitpoint()
        print(sta.ifconfig())
        ip = sta.ifconfig()[0]
        return ip
    else:
        a=network.LAN()
        if not a.active():
            raise RuntimeError("LAN interface is not active.")
        a.ifconfig("dhcp")
        print(a.ifconfig())
        ip = a.ifconfig()[0]
        return ip


# 自定义人体关键点检测类
class PersonKeyPointApp(AIBase):
    def __init__(self,kmodel_path,model_input_size,confidence_threshold=0.2,nms_threshold=0.5,rgb888p_size=[1280,720],display_size=[1920,1080],debug_mode=0):
        super().__init__(kmodel_path,model_input_size,rgb888p_size,debug_mode)
        self.kmodel_path=kmodel_path
        # 模型输入分辨率
        self.model_input_size=model_input_size
        # 置信度阈值设置
        self.confidence_threshold=confidence_threshold
        # nms阈值设置
        self.nms_threshold=nms_threshold
        # sensor给到AI的图像分辨率
        self.rgb888p_size=[ALIGN_UP(rgb888p_size[0],16),rgb888p_size[1]]
        # 显示分辨率
        self.display_size=[ALIGN_UP(display_size[0],16),display_size[1]]
        self.debug_mode=debug_mode
        #骨骼信息
        self.SKELETON = [(16, 14),(14, 12),(17, 15),(15, 13),(12, 13),(6,  12),(7,  13),(6,  7),(6,  8),(7,  9),(8,  10),(9,  11),(2,  3),(1,  2),(1,  3),(2,  4),(3,  5),(4,  6),(5,  7)]
        #肢体颜色
        self.LIMB_COLORS = [(255, 51,  153, 255),(255, 51,  153, 255),(255, 51,  153, 255),(255, 51,  153, 255),(255, 255, 51,  255),(255, 255, 51,  255),(255, 255, 51,  255),(255, 255, 128, 0),(255, 255, 128, 0),(255, 255, 128, 0),(255, 255, 128, 0),(255, 255, 128, 0),(255, 0,   255, 0),(255, 0,   255, 0),(255, 0,   255, 0),(255, 0,   255, 0),(255, 0,   255, 0),(255, 0,   255, 0),(255, 0,   255, 0)]
        #关键点颜色，共17个
        self.KPS_COLORS = [(255, 0,   255, 0),(255, 0,   255, 0),(255, 0,   255, 0),(255, 0,   255, 0),(255, 0,   255, 0),(255, 255, 128, 0),(255, 255, 128, 0),(255, 255, 128, 0),(255, 255, 128, 0),(255, 255, 128, 0),(255, 255, 128, 0),(255, 51,  153, 255),(255, 51,  153, 255),(255, 51,  153, 255),(255, 51,  153, 255),(255, 51,  153, 255),(255, 51,  153, 255)]

        # Ai2d实例，用于实现模型预处理
        self.ai2d=Ai2d(debug_mode)
        # 设置Ai2d的输入输出格式和类型
        self.ai2d.set_ai2d_dtype(nn.ai2d_format.NCHW_FMT,nn.ai2d_format.NCHW_FMT,np.uint8, np.uint8)

    # 配置预处理操作，这里使用了pad和resize，Ai2d支持crop/shift/pad/resize/affine，具体代码请打开/sdcard/app/libs/AI2D.py查看
    def config_preprocess(self,input_image_size=None):
        with ScopedTiming("set preprocess config",self.debug_mode > 0):
            # 初始化ai2d预处理配置，默认为sensor给到AI的尺寸，您可以通过设置input_image_size自行修改输入尺寸
            ai2d_input_size=input_image_size if input_image_size else self.rgb888p_size
            top,bottom,left,right=self.get_padding_param()
            self.ai2d.pad([0,0,0,0,top,bottom,left,right], 0, [0,0,0])
            self.ai2d.resize(nn.interp_method.tf_bilinear, nn.interp_mode.half_pixel)
            self.ai2d.build([1,3,ai2d_input_size[1],ai2d_input_size[0]],[1,3,self.model_input_size[1],self.model_input_size[0]])

    # 自定义当前任务的后处理
    def postprocess(self,results):
        with ScopedTiming("postprocess",self.debug_mode > 0):
            # 这里使用了aidemo库的person_kp_postprocess接口
            results = aidemo.person_kp_postprocess(results[0],[self.rgb888p_size[1],self.rgb888p_size[0]],self.model_input_size,self.confidence_threshold,self.nms_threshold)
            return results

    #绘制结果，绘制人体关键点
    def draw_result(self,pl,res):
        with ScopedTiming("display_draw",self.debug_mode >0):
            if res[0]:
                pl.osd_img.clear()
                kpses = res[1]
                for i in range(len(res[0])):
                    for k in range(17+2):
                        if (k < 17):
                            kps_x,kps_y,kps_s = round(kpses[i][k][0]),round(kpses[i][k][1]),kpses[i][k][2]
                            kps_x1 = int(float(kps_x) * self.display_size[0] // self.rgb888p_size[0])
                            kps_y1 = int(float(kps_y) * self.display_size[1] // self.rgb888p_size[1])
                            if (kps_s > 0):
                                pl.osd_img.draw_circle(kps_x1,kps_y1,5,self.KPS_COLORS[k],4)
                        ske = self.SKELETON[k]
                        pos1_x,pos1_y= round(kpses[i][ske[0]-1][0]),round(kpses[i][ske[0]-1][1])
                        pos1_x_ = int(float(pos1_x) * self.display_size[0] // self.rgb888p_size[0])
                        pos1_y_ = int(float(pos1_y) * self.display_size[1] // self.rgb888p_size[1])

                        pos2_x,pos2_y = round(kpses[i][(ske[1] -1)][0]),round(kpses[i][(ske[1] -1)][1])
                        pos2_x_ = int(float(pos2_x) * self.display_size[0] // self.rgb888p_size[0])
                        pos2_y_ = int(float(pos2_y) * self.display_size[1] // self.rgb888p_size[1])

                        pos1_s,pos2_s = kpses[i][(ske[0] -1)][2],kpses[i][(ske[1] -1)][2]
                        if (pos1_s > 0.0 and pos2_s >0.0):
                            pl.osd_img.draw_line(pos1_x_,pos1_y_,pos2_x_,pos2_y_,self.LIMB_COLORS[k],4)
                    gc.collect()
            else:
                pl.osd_img.clear()

    # 计算padding参数
    def get_padding_param(self):
        dst_w = self.model_input_size[0]
        dst_h = self.model_input_size[1]
        input_width = self.rgb888p_size[0]
        input_high = self.rgb888p_size[1]
        ratio_w = dst_w / input_width
        ratio_h = dst_h / input_high
        if ratio_w < ratio_h:
            ratio = ratio_w
        else:
            ratio = ratio_h
        new_w = (int)(ratio * input_width)
        new_h = (int)(ratio * input_high)
        dw = (dst_w - new_w) / 2
        dh = (dst_h - new_h) / 2
        top = int(round(dh - 0.1))
        bottom = int(round(dh + 0.1))
        left = int(round(dw - 0.1))
        right = int(round(dw - 0.1))
        return  top, bottom, left, right

    def pose2dict(self, poses):
        res = poses
        if len(res[0])<1:
            pose_dict = {}
        else:
            # print(res)
            kpses = res[1]
            pose_dict = {key:np.array([int(float(kpses[0][body_mapper[key]][0]) * self.display_size[0] // self.rgb888p_size[0]), int(float(kpses[0][body_mapper[key]][1]) * self.display_size[1] // self.rgb888p_size[1])]) for key in body_mapper.keys()}

        return pose_dict

# 计算余弦相似度
def calculate_cosine_similarity(v1, v2):
    # 计算两个向量的点积

    dot_product = np.dot(np.array(v1), np.array(v2))

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

def state2words(state):
    words_list = []

    # state to list of words
    if 11 in state:
        words_list.append('s')
    elif 3 in state and 4 in state: # 向前
        words_list.append('w')
    elif 3 in state:
        words_list.append('d')
    elif 4 in state:
        words_list.append('a')
    else:
        pass

    # 左右
    if 1 in state:
        words_list.append('j') # 平A
    if 2 in state:
        words_list.append('k') # 闪避

    if 9 in state:
        words_list.append('e') # e技能
    if 10 in state:
        words_list.append('q') # q技能

    if 5 in state:
        words_list.append('i') # 确认
    if 6 in state:
        words_list.append('o') # 取消

    if 7 in state:
        words_list.append('n') # 向右转
    if 8 in state:
        words_list.append('m') # 向左转

    return words_list

def words2bytes(words_list):
    bytes_list = [words2bytes_dict.get(x, 0x00) for x in words_list]

    return bytes_list

def state2bytes(state):
    words_list = state2words(state)
    bytes_list = words2bytes(words_list)


    return bytes_list

def bytes2command(data_list):
    """
    生成符合指定协议格式的二进制命令包

    参数:
        data_list (list): 要发送的数据列表，每个元素应为0-255的整数

    返回:
        bytes: 完整的二进制命令包
    """
    data_list = [0x00] if len(data_list) == 0 else data_list
    data_list = [0x00] * (8 - len(data_list)) + data_list # 补零，避免无反应

    # 固定帧头 (2字节)
    header = [0x57, 0xAB]

    # 地址字段 (1字节)
    addr = 0x00

    # 命令字段 (1字节)
    cmd = 0x02

    # 数据长度字段 (1字节)
    data_length = len(data_list)

    # 转换数据列表为字节 (自动处理0-255范围)
    data_bytes = data_list

    # 计算校验和：地址 + 命令 + 数据长度 + 所有数据字节的和 (1字节)
    checksum = (sum(header) + addr + cmd + data_length + sum(data_bytes)) % 256
    # 组装完整数据包
    packet = (bytes(header) + # 帧头
        bytes([addr, cmd, data_length]) +  # 地址、命令、长度
        bytes(data_bytes) +              # 数据部分
        bytes([checksum])         # 校验和
    )
    print(packet)

    return packet



def send_command(server_ip='192.168.2.121', port=80, command="", timeout=1, ifencode=False):
    global last_command
    if last_command == command:
        return
    else:
        last_command = command

    try:
        #建立socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        #获取地址及端口号 对应地址
        ai = socket.getaddrinfo(server_ip, port)
        addr = ai[0][-1]
        s.connect(addr)
        print("send", command)
        s.write(command)
        time.sleep(0.05)
        s.close()
    except:
        # 连接失败（包括超时）
        print(f"Connection error!")

# 假设的图像处理函数，返回一个整数 N
def process_frame(poses):
    if len(poses) == 0:
        return ""
    gesture_list = posedict2state(poses, type=DEBUG_FLAG)
    bytes_list = state2bytes(gesture_list)
    command = bytes2command(bytes_list)
    if IF_SEND_COMMAND:
        send_command(server_ip=server_ip, port=port, command=command)
    return "/".join([str(x) for x in gesture_list])  # 示例返回值

if __name__=="__main__":
    network_use_wlan(True)

    # 显示模式，默认"hdmi",可以选择"hdmi"和"lcd"
    display_mode="lcd"
    # k230保持不变，k230d可调整为[640,360]
    rgb888p_size = [1920, 1080]

    if display_mode=="hdmi":
        display_size=[1920,1080]
    else:
        display_size=[800,480]
    # 模型路径
    kmodel_path="/sdcard/examples/kmodel/yolov8n-pose.kmodel"
    # 其它参数设置
    confidence_threshold = 0.2
    nms_threshold = 0.5
    # 初始化PipeLine
    pl=PipeLine(rgb888p_size=rgb888p_size,display_size=display_size,display_mode=display_mode)
    pl.create()
    # 初始化自定义人体关键点检测实例
    person_kp=PersonKeyPointApp(kmodel_path,model_input_size=[320,320],confidence_threshold=confidence_threshold,nms_threshold=nms_threshold,rgb888p_size=rgb888p_size,display_size=display_size,debug_mode=0)
    person_kp.config_preprocess()
    while True:
        with ScopedTiming("total",1):
            # 获取当前帧数据
            img=pl.get_frame()
            # 推理当前帧
            res=person_kp.run(img)
            pose_dict = person_kp.pose2dict(res)
            gesture_str = process_frame(pose_dict)
            print(gesture_str)

            # 绘制结果到PipeLine的osd图像
            person_kp.draw_result(pl,res)
            # 显示当前的绘制结果
            pl.show_image()
            gc.collect()
    person_kp.deinit()
    pl.destroy()

