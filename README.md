# CameraUSBHid
基于微控制器和姿态检测的体感输入器。

该仓库基于姿态检测获取人物的姿态信息，并通过USB HID协议发送到PC端，替代键盘输入，从而实现体感输入。

![workflow.png](Docs/workflow.png)

## 开发环境
> 不重要，只是摆在这里而已
- 开发语言为Python 和 Micropython
- 运算设备: 带有WIFI与摄像头模块(例如电脑、CanMV-K230)
- 微控制器: 带有WIFI功能(例如树莓派Pico W/WH)
- CH9329 串口转标准 USB HID 设备(大约10块钱)

## 快速开始
你可以参考本章节快速开始，章节中的每个部分都是可替换的，你可以遵循以下步骤有一个基础的认识。

### 设备准备

- 电脑(带有摄像头、能够连接到局域网)
- 树莓派Pico W 或 树莓派Pico WH，如需复刻本项目，请确保引脚0和引脚1是可用的
- CH9329 串口转标准 USB HID 设备

### 硬件设备连接
#### 基于杜邦线连接树莓派Pico W 与 CH9329(新手推荐)
首先，你需要将树莓派Pico W 与 CH9329 连接起来，在测试阶段可以采用杜邦线进行连接，这种方式的好处在于不需要自己焊接，购买成品散件即可。但这种方式的缺点在于连线比较散乱，树莓派 Pico W 和 CH9329 不共享供电，因此使用时，还需要额外为 树莓派Pico W 提供电源。

连接方式如下：

|树莓派Pico W引脚| CH9329|
|:---:|:---:|
|GP0 | RXD |
|GP1 | TXD |

![example1.png](Docs/example1.png)

#### 基于嘉立创打板连接树莓派Pico W 与 CH9329(进阶推荐)
为了让硬件连接更加紧凑（主要是为了他们能够共享供电），你可以选择在嘉立创打板。(作者比较懒，还没在嘉立创公开项目，如果你对这个项目感兴趣可以催我，让我在嘉立创公开对应的PCB设计文件)

打板后，只需要焊接5个元器件（立创商城可以一键下单）即可：

|     名称     |         型号名         | 数量 |
|:----------:|:-------------------:|:--:|
|   USB公头    | U217-041N-4BV81 | 1  |
| 贴片电容 10uf  | CL21A106KOQNNNE | 1  |
| 贴片电容 0.1uf | CL05B104KO5NNNC | 2  |
|   CH9329   | CH9329 | 1  |

![example2.png](Docs/example2.png)

### 硬件设备软件配置
> 如果你第一次使用微控制器，可以参考 https://pico.org.cn/ 中 "如何在 Pico 上使用 MicroPython"，只需要简单3分钟即可快速入门。
- 下载 [Thonny](https://thonny.org/) 并安装，打开 Thonny 并连接到 树莓派Pico W 或 树莓派Pico WH。
- 修改 LowerMachine/CH9329Sever.py 文件末尾的 WIFI账号和密码为你的WIFI账号和密码信息。
- 将 LowerMachine/CH9329Sever.py 保存到树莓派Pico W 或 树莓派Pico WH 中，保存为 main.py。
- 在 Thonny 中运行 main.py。
- 在 Thonny 中读取输出的 IP 地址，并记录这个地址（后面会用到）。

### 软件设备配置
#### 安装依赖
```bash
pip install -r requirements.txt
```

#### 配置
将 main.pyqt.py 中 server_ip 变量改为你在树莓派Pico W 或 树莓派Pico WH 中输出的 IP 地址。

### 运行与测试
1. 将 main.pyqt.py 中 IF_SEND_COMMAND 改为 False, DEBUG_FLAG 改为 debug，运行 main.pyqt.py, 你将在电脑上看到画面，在画面中做出叉腰、摸头的动作，界面上会显示姿态名称。 
2. 将 main.pyqt.py 中 IF_SEND_COMMAND 改为 True, DEBUG_FLAG 改为 debug，运行 main.pyqt.py, 你将在电脑上看到画面，在画面中做出叉腰、摸头的动作，界面上会显示对应的数字。 
3. 将 下位机硬件 接入被控设备中，打开 记事本，运行 main.pyqt.py, 你将在电脑上看到画面，在画面中做出叉腰、摸头的动作，电脑上的记事本会打印对应的字符。
4. 打开游戏（例如愿神），运行 main.pyqt.py, 游戏角色将会随着你的动作进行移动。

### 动作与配置
当前支持检测的动作可以参考 Source/id.json，每种动作对饮过的姿态可以参考 Source/Images，姿态与键盘输入的对应关系参考 Tools/state2bytes_vector.py。

## 调试与自定义
你可以通过 debug.gradio.py 配置、记录新的姿势，并生成对应的配置文件 Source/configs.json，之后，仅需要修改 Tools/state2bytes_vector.py 中姿势和键盘输入的对应关系即可。

## 模型来源
更多信息请参考
- https://github.com/openvinotoolkit/open_model_zoo/blob/master/demos/human_pose_estimation_demo/python/README.md
- https://github.com/openvinotoolkit/openvino_notebooks/blob/latest/notebooks/pose-estimation-webcam/pose-estimation.ipynb
- https://storage.openvinotoolkit.org/repositories/open_model_zoo/2022.1/models_bin/3/human-pose-estimation-0001/FP16-INT8/
- https://github.com/PaddlePaddle/PaddleDetection/blob/release/2.5/configs/keypoint/tiny_pose/README.md