import json
import os

import gradio as gr
import pandas as pd



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

# 构建 Gradio 界面
with gr.Blocks() as demo:
    gr.Markdown("# 动作按键配置表格")
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
        dropdown_key = gr.Dropdown(choices=[chr(i) for i in range(ord('a'), ord('z') + 1)], value="a", label="选择按键", interactive=True)
    with gr.Row():
        btn_add_action = gr.Button("添加动作")
        btn_delete_action = gr.Button("清空动作")
        btn_add_key = gr.Button("添加按键")
        btn_delete_key = gr.Button("清空按键")
    with gr.Row():
        btn_new_line = gr.Button("新增行")
        btn_delete_line = gr.Button("删除行")


    # 按钮点击事件
    btn_generate_table.click(fn=fn_generate_table,inputs=[],outputs=[table_data, table_state, dropdown_line, dropdown_action])
    btn_read_table.click(fn=fn_read_table,inputs=[],outputs=[table_data, table_state, dropdown_line, dropdown_action])
    btn_save_table.click(fn=fn_save_table,inputs=[table_data, table_state],outputs=[])
    btn_add_action.click(fn=fn_add_action, inputs=[table_data, dropdown_line, dropdown_action], outputs=[table_data])
    btn_delete_action.click(fn=fn_delete_action, inputs=[table_data, dropdown_line], outputs=[table_data])
    btn_add_key.click(fn=fn_add_key, inputs=[table_data, dropdown_line, dropdown_key], outputs=[table_data])
    btn_delete_key.click(fn=fn_delete_key, inputs=[table_data, dropdown_line], outputs=[table_data])
    btn_new_line.click(fn=fn_table_new_line, inputs=[table_data], outputs=[table_data, dropdown_line])
    btn_delete_line.click(fn=fn_table_delete_line, inputs=[table_data, dropdown_line], outputs=[table_data, dropdown_line])

# 启动 Gradio 应用
demo.launch()