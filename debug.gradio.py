import gradio as gr
from Tools.state2bytes import words2bytes
from Tools.bytes2command import bytes2command
from Tools.sendcommand import send_command

with gr.Blocks() as App:
    gr.Markdown("# 摄像头鼠标调试工具")
    with gr.Tab("鼠标远程控制"):
        txt_url = gr.Textbox(label="远程鼠标调试地址", value="192.168.2.184")
        txt_port = gr.Number(label="远程鼠标调试端口", value=80)
        txt_words = gr.Textbox(label="远程鼠标调试字符(自动补位-长度不够则自动补齐长度)", value="a")
        btn_send = gr.Button("发送")

        btn_send.click(fn=lambda x,y,z: send_command(x, y, bytes2command(words2bytes(z))), inputs=[txt_url, txt_port, txt_words], outputs=[])
    with gr.Tab("Yolo检测调试"):
        img_raw = gr.Image(label="人物画面")
        img_keypoints = gr.Image(label="人物关键点")

        btn_detect = gr.Button("检测")

        btn_detect.click(fn=lambda x,y: detect_image(x, y), inputs=[img_raw, img_keypoints], outputs=[])
App.launch()