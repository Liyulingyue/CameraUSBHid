import json
import os

import cv2
import gradio as gr
import numpy as np

from Tools.state2bytes import words2bytes
from Tools.bytes2command import bytes2command
from Tools.sendcommand import send_command
from Tools.sendcommand import send_commands_timeout as send_command

# from Tools.ov.Estimator import HumanPoseEstimator, draw_poses
# from Tools.ov.utils import body_mapper
# model_path = "Models/human-pose-estimation-0001/FP16-INT8/human-pose-estimation-0001.xml"
# device = "CPU"
# estimator = HumanPoseEstimator(model_path, device)

from Tools.fastdeploy.utils import body_mapper, draw_poses
from Tools.fastdeploy.Estimator import HumanPoseEstimator
model_path = "Models/tinypose_128x96"
device = "CPU"
estimator = HumanPoseEstimator(model_path, device)


def fn_btn_save(img_raw, name, index, basekeypoints, list_corekeypoints):
    result, _ = estimator.infer(img_raw, False)

    # 生成一张形状和img_raw相同的纯黑图片
    img_black = np.zeros((img_raw.shape[0], img_raw.shape[1], 3), dtype=np.uint8)
    img_demo = draw_poses(img_black, result, point_score_threshold=0.1)

    # 计算每个关键点的相对位置
    value_dict = {key: (0, 0) for key in list_corekeypoints}
    base_value = result[0, body_mapper[basekeypoints], :2]
    for key in value_dict:
        key_value = result[0, body_mapper[key], :2]
        value_dict[key] = (key_value - base_value).tolist()

    # 记录信息
    pose_info = {
        'name': name,
        'index': int(index),
        'basekeypoints': basekeypoints,
        'list_corekeypoints': list_corekeypoints,
        'value_dict': value_dict,
        'model_raw_results': result.tolist()
    }

    cv2.imwrite(f"Source/Images/{name}_{index}.jpg", img_demo)
    json.dump(pose_info, open(f"Source/RawInfo/{name}_{index}.json", 'w'), indent=4)

def fn_btn_generate_config():
    raw_info_path = "Source/RawInfo"
    config_path = "Source/configs.json"
    id_path = "Source/id.json"
    configs = []
    id_list = {}
    for file_name in os.listdir(raw_info_path):
        if not file_name.endswith(".json"): continue
        info = json.load(open(os.path.join(raw_info_path, file_name)))
        configs.append({
            'name': info['name'],
            'index': info['index'],
            'basekeypoints': info['basekeypoints'],
            'list_corekeypoints': info['list_corekeypoints'],
            'value_dict': info['value_dict']
        })
        id_list[info['index']] = info['name']
    json.dump(configs, open(config_path, 'w'), indent=4)
    json.dump(id_list, open(id_path, 'w'), indent=4)

with gr.Blocks() as App:
    gr.Markdown("# 摄像头鼠标调试工具")
    with gr.Tab("鼠标远程控制"):
        txt_url = gr.Textbox(label="远程鼠标调试地址", value="192.168.2.184")
        txt_port = gr.Number(label="远程鼠标调试端口", value=80)
        txt_words = gr.Textbox(label="远程鼠标调试字符(自动补位-长度不够则自动补齐长度)", value="a")
        btn_send = gr.Button("发送")

        btn_send.click(fn=lambda x,y,z: send_command(x, y, bytes2command(words2bytes(z))), inputs=[txt_url, txt_port, txt_words], outputs=[])
    with gr.Tab("Yolo检测调试"):
        with gr.Row():
            img_raw = gr.Image(label="人物画面")
            img_keypoints = gr.Image(label="人物关键点")
        btn_detect = gr.Button("检测")
        with gr.Row():
            txt_posename = gr.Textbox(label="姿势名称")
            txt_index = gr.Number(label="索引")
            txt_basekeypoints = gr.Dropdown(label="基准关键点", choices=body_mapper.keys(), interactive=True)
        txt_list_corekeypoints = gr.CheckboxGroup(label="核心关键点", choices=body_mapper.keys())
        btn_save = gr.Button("将姿态信息保存为模板文件(Source/Images[RawInfo])")
        btn_generate_config = gr.Button("生成配置文件(Source/configs.json)")

        btn_detect.click(fn=lambda x: estimator.infer(x, True)[1], inputs=[img_raw], outputs=[img_keypoints])
        btn_save.click(fn=fn_btn_save, inputs=[img_raw, txt_posename, txt_index, txt_basekeypoints, txt_list_corekeypoints], outputs=[])
        btn_generate_config.click(fn=fn_btn_generate_config, inputs=[], outputs=[])


App.launch()