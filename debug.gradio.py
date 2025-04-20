import json
import os

import cv2
import gradio as gr
import numpy as np
import pandas as pd

from Tools.state2bytes import words2bytes
from Tools.bytes2command import bytes2command
from Tools.sendcommand import send_command
from Tools.sendcommand import send_command_timeout as send_command

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

key_choices_list = [chr(i) for i in range(ord('a'), ord('z') + 1)] + [int(i) for i in range(10)] + ["LeftMouse"]


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

# 生成表格数据
def fn_generate_table():
    folder_path = "Source/RawInfo"
    if not os.path.exists(folder_path):
        print(f"文件夹 {folder_path} 不存在！")
        return

    actions_map = {}
    table_lines = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".json"):
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                action_name = data["name"]
                action_index = data["index"]
                actions_map[action_name] = action_index
                table_lines.append([0, action_name, ""]) # 行号，动作名称，按键
    # 更新序号为行号
    for i, line in enumerate(table_lines):
        line[0] = i + 1
    table_data = pd.DataFrame(table_lines, columns=["序号", "动作名称", "按键"])
    dropdown_line_options = range(1, len(table_lines) + 1)
    line_option = gr.Dropdown(choices=dropdown_line_options, value=1, label="选择行", interactive=True)
    action_option = gr.Dropdown(choices=actions_map, label="选择动作", interactive=True)
    return table_data, actions_map, line_option, action_option

def fn_read_table():
    input_path = "Source/mapper.json"
    if not os.path.exists(input_path):
        print(f"文件 {input_path} 不存在！")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        mapper_list = data["mapper"]
        actions_map = data["table_state"]

    table_lines = []
    for mapper in mapper_list:
        action_numbers = mapper["action"]
        # 将action_numbers转换为字符串，便利actions_map，若取值与number一致，则为对应的action
        action_names = []
        for number in action_numbers:
            for action, index in actions_map.items():
                if index == number:
                    action_names.append(action)
                    break
        keys = mapper["keys"]
        table_lines.append([0, ";".join(action_names), ";".join(keys)])
    # 更新序号为行号
    for i, line in enumerate(table_lines):
        line[0] = i + 1
    table_data = pd.DataFrame(table_lines, columns=["序号", "动作名称", "按键"])
    dropdown_line_options = range(1, len(table_lines) + 1)
    line_option = gr.Dropdown(choices=dropdown_line_options, value=1, interactive=True)
    action_option = gr.Dropdown(choices=actions_map, label="选择动作", interactive=True)
    return table_data, actions_map, line_option, action_option

def fn_save_table(table_data, table_state):
    output_path = "Source/mapper.json"

    mapper_list = []
    for i, row in table_data.iterrows():
        table_action = row[1]
        table_key = row[2]
        table_action_list = table_action.split(";")
        table_key_list = table_key.split(";")
        number_list = []
        key_list = []
        for action in table_action_list:
            if action in table_state:
                number_list.append(table_state[action])
        for key in table_key_list:
            if key != "":
                key_list.append(key)
        if table_action_list != [] and key_list != []:
            mapper_list.append({
                "action": number_list,
                "keys": key_list,
            })

    output_dict = {
        "mapper": mapper_list,
        "table_state": table_state
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_dict, f, ensure_ascii=False, indent=4)


def fn_table_new_line(table_data):
    new_row = [len(table_data) + 1, "", ""]
    table_data.loc[len(table_data)] = new_row
    line_option = gr.Dropdown(choices=range(1, len(table_data) + 1), value=1, label="选择行", interactive=True)
    return table_data, line_option

def fn_table_delete_line(table_data, line_option):
    selected_index = int(line_option) - 1
    table_data = table_data.drop(selected_index)
    for i in range(len(table_data)):
        table_data.iloc[i, 0] = i + 1
    line_option = gr.Dropdown(choices=range(1, len(table_data) + 1), value=1, label="选择行", interactive=True)
    return table_data, line_option

def fn_add_action(table_data, line_option, action_option):
    selected_index = int(line_option) - 1
    action_value = table_data.iloc[selected_index, 1]
    if action_option != "":
        table_data.iloc[selected_index, 1] = action_value + ";" + action_option if action_value != "" else action_option
    return table_data

def fn_delete_action(table_data, line_option):
    selected_index = int(line_option) - 1
    table_data.iloc[selected_index, 1] = ""
    return table_data

def fn_add_key(table_data, line_option, key_option):
    selected_index = int(line_option) - 1
    key_value = table_data.iloc[selected_index, 2]
    if key_option != "":
        table_data.iloc[selected_index, 2] = key_value + ";" + key_option if key_value != "" else key_option
    return table_data

def fn_delete_key(table_data, line_option):
    selected_index = int(line_option) - 1
    table_data.iloc[selected_index, 2] = ""
    return table_data


with gr.Blocks() as App:
    gr.Markdown("# 摄像头鼠标调试工具")
    with gr.Tab("鼠标远程控制"):
        gr.Markdown("""
        本页面可以通过发送指令的方式控制远程鼠标
        """)
        txt_url = gr.Textbox(label="远程鼠标调试地址", value="192.168.2.184")
        txt_port = gr.Number(label="远程鼠标调试端口", value=80)
        txt_words = gr.Textbox(label="远程鼠标调试字符(自动补位-长度不够则自动补齐长度)", value="a")
        btn_send = gr.Button("发送")

        btn_send.click(fn=lambda x,y,z: send_command(x, y, bytes2command(words2bytes(z))), inputs=[txt_url, txt_port, txt_words], outputs=[])
    with gr.Tab("Yolo检测调试"):
        gr.Markdown("""
        使用姿态检测网络，检测出人物，并生成姿态模板文件
        """)

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
        btn_generate_config = gr.Button("将所有模板文件生成配置文件(Source/configs.json)")

        btn_detect.click(fn=lambda x: estimator.infer(x, True)[1], inputs=[img_raw], outputs=[img_keypoints])
        btn_save.click(fn=fn_btn_save, inputs=[img_raw, txt_posename, txt_index, txt_basekeypoints, txt_list_corekeypoints], outputs=[])
        btn_generate_config.click(fn=fn_btn_generate_config, inputs=[], outputs=[])

    with gr.Tab("姿态与动作映射配置"):
        gr.Markdown("""
        本页面用于配置姿态与动作的映射关系
        """)

        table_state = gr.State(value=None)
        table_data = gr.Dataframe(
            value=None,  # 初始为空
            headers=["序号", "动作名称", "按键"],
            interactive=False  # 表格不可直接编辑
        )
        with gr.Row():
            btn_generate_table = gr.Button("生成表格")
            btn_read_table = gr.Button("读取表格")
            btn_save_table = gr.Button("保存表格")

        with gr.Row():
            dropdown_line = gr.Dropdown(choices=[], value=1, label="选择行", interactive=True)
            dropdown_action = gr.Dropdown(choices=[], label="选择动作", interactive=True)
            dropdown_key = gr.Dropdown(choices=key_choices_list, value="a",
                                       label="选择按键", interactive=True)
        with gr.Row():
            btn_add_action = gr.Button("添加动作")
            btn_delete_action = gr.Button("清空动作")
            btn_add_key = gr.Button("添加按键")
            btn_delete_key = gr.Button("清空按键")
        with gr.Row():
            btn_new_line = gr.Button("新增行")
            btn_delete_line = gr.Button("删除行")

        # 按钮点击事件
        btn_generate_table.click(fn=fn_generate_table, inputs=[],
                                 outputs=[table_data, table_state, dropdown_line, dropdown_action])
        btn_read_table.click(fn=fn_read_table, inputs=[],
                             outputs=[table_data, table_state, dropdown_line, dropdown_action])
        btn_save_table.click(fn=fn_save_table, inputs=[table_data, table_state], outputs=[])
        btn_add_action.click(fn=fn_add_action, inputs=[table_data, dropdown_line, dropdown_action],
                             outputs=[table_data])
        btn_delete_action.click(fn=fn_delete_action, inputs=[table_data, dropdown_line], outputs=[table_data])
        btn_add_key.click(fn=fn_add_key, inputs=[table_data, dropdown_line, dropdown_key], outputs=[table_data])
        btn_delete_key.click(fn=fn_delete_key, inputs=[table_data, dropdown_line], outputs=[table_data])
        btn_new_line.click(fn=fn_table_new_line, inputs=[table_data], outputs=[table_data, dropdown_line])
        btn_delete_line.click(fn=fn_table_delete_line, inputs=[table_data, dropdown_line],
                              outputs=[table_data, dropdown_line])

App.launch()