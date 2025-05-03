import ujson as json
import uos as os
import network
import usocket as socket
import time
from machine import Pin, UART, I2C
from ssd1306 import SSD1306_I2C
import bluetooth

# 配置 UART
uart = UART(1, baudrate=9600, tx=Pin(0), rx=Pin(1))
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)
oled = SSD1306_I2C(128, 32, i2c)

# 配置蓝牙相关信息
ble = bluetooth.BLE()  # 创建BLE设备
BLE_NAME = "CameraUSBHid"  # 蓝牙名称
adv_mode = bytearray(b'\x02\x01\x06')  # 正常蓝牙模式, ad struct 1

# 配置服务器监听IP
IP_self = "0.0.0.0"

# 默认配网信息
cfg_dict_default = {  # 默认字典
    "BLE": 1,  # 默认蓝牙配网模式
    "SSID": "",  # 默认没有wifi信息
    "PASSWORD": "",  # 默认没有wifi密码
}
config = {}  # 配置信息


# ***************** 开机状态设置 ***************
def load_config():
    # 开机初始化配置文件信息
    cfg_dict = cfg_dict_default.copy()
    # 检查文件是否存在
    if 'cfg.json' in os.listdir():
        with open('cfg.json', 'r') as f:
            loaded_data = json.load(f)
        # 验证读取的数据是否是字典类型
        if isinstance(loaded_data, dict):
            cfg_dict.update(loaded_data)

    # 配置为蓝牙配网状态，写入文件
    with open('cfg.json', 'w') as f:
        json.dump(cfg_dict_default, f)

    # 等待2秒，此时重启，下次读取数据时，会变为蓝牙配网模式
    oled.fill(0)
    oled.text("Loading", 0, 12)
    oled.show()
    time.sleep(2)

    # 2s内没有重启，还原数据模式
    with open('cfg.json', 'w') as f:
        json.dump(cfg_dict, f)

    return cfg_dict


# ***************** 蓝牙配网状态设置 ***************
# BLE相应时间
def ble_irq(event, data):  # 蓝牙中断函数
    if event == 1:  # 蓝牙已连接
        # 作为外设设备，一旦被中心设备连接之后就无法再被其他设备连接，所以conn_handle只能为0
        conn_handle, addr_type, addr = data
        print(f"fd = [{conn_handle}] connect")
        oled.fill(0)
        oled.text("BLE Connect", 0, 12)
        oled.show()

    elif event == 2:  # 蓝牙断开连接
        conn_handle, addr_type, addr = data
        print(f"fd = [{conn_handle}] disconnect")
        ble.gap_advertise(100, adv_data=adv_data)
        oled.fill(0)
        oled.text("BLE Disconnect", 0, 12)
        oled.show()

    elif event == 3:  # 收到数据
        # 作为中心设备，可能会连接很多外设设备，即各种各样的服务，例如hid服务，env服务，battery服务等，通过conn_handle来区分是哪个设备（服务）发来的数据
        # 通过attr_handle来区分收到的是哪个特性的数据
        conn_handle, attr_handle = data
        print(f"fd = [{conn_handle}], char = [{attr_handle}] recive msg")
        buffer = ble.gatts_read(attr_handle)
        msg = buffer.decode('UTF-8').strip()
        print(msg)
        if msg.count(",") == 1:
            SSID, PASSWORD = msg.split(",")
            config["BLE"] = 0
            config["SSID"] = SSID
            config["PASSWORD"] = PASSWORD
            with open('cfg.json', 'w') as f:
                json.dump(config, f)
            oled.fill(0)
            oled.text("PLEASE REBOOT", 0, 12)
            oled.show()


def connect_to_ble():
    ble.active(True)  # 打开BLE
    adv_mode = bytearray(b'\x02\x01\x06')  # 正常蓝牙模式, ad struct 1

    name = BLE_NAME.encode()  # 编码成utf-8格式
    adv_name = bytearray((len(name) + 1, 0x09)) + name  # 0x09是蓝牙名称,ad struct 2
    adv_data = adv_mode + adv_name

    UART_UUID = bluetooth.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
    UART_TX = (bluetooth.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E'), bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY,)
    UART_RX = (bluetooth.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E'), bluetooth.FLAG_WRITE,)
    UART_SERVICE = (UART_UUID, (UART_TX, UART_RX,),)
    SERVICES = (UART_SERVICE,)
    ((tx, rx,),) = ble.gatts_register_services(SERVICES)

    ble.gap_advertise(100, adv_data=adv_data)

    oled.fill(0)
    oled.text("BLE:" + BLE_NAME, 0, 12)
    oled.show()

    ble.irq(ble_irq)

    while (1):
        time.sleep(0.1)


# ***************** WIFI通讯设置 ***************
def connect_to_wifi(ssid, password):
    oled.fill(0)
    oled.text("Connecting WIFI", 0, 12)
    oled.show()

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        print('当前已连接到 Wi-Fi，正在断开连接...')
        wlan.disconnect()
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        time.sleep(1)
        print("connecting")
    print('WiFi connected')
    print('IP address:', wlan.ifconfig()[0])
    IP_self = wlan.ifconfig()[0]

    oled.fill(0)
    oled.text(wlan.ifconfig()[0], 0, 12)
    oled.show()


def flush_uart_buffer():
    while uart.any():
        uart.read()  # 一次性读取所有积压数据


def start_server():
    # 创建套接字并绑定到端口80 TCP
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 80))
    s.listen(5)
    print('Listening on socket...')

    while True:
        print("Listening")
        conn, addr = s.accept()
        print('Connected by', addr)
        request = conn.recv(1024)
        print('Receive:', request)

        conn.close()

        # 转发给CH9329
        uart.write(request)
        flush_uart_buffer()  # 清空未读数据


def main():
    # 使用示例
    global config
    config = load_config()
    print(config)
    if_ble_model = config.get('BLE', 1)  # 默认为配网模式
    if if_ble_model == 1:
        connect_to_ble()
    else:
        # 连接到 Wi-Fi， WIFI名称、密码
        Wifi_Name = config.get('SSID', "******")
        Wifi_Password = config.get('PASSWORD', "******")
        connect_to_wifi(Wifi_Name, Wifi_Password)
        # 启动服务器
        start_server()


if __name__ == '__main__':
    main()

