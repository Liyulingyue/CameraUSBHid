import network
import usocket as socket
import time
from machine import Pin, UART, I2C
from ssd1306 import SSD1306_I2C

# 配置 UART
uart = UART(1, baudrate=9600, tx=Pin(0), rx=Pin(1))
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)
oled = SSD1306_I2C(128, 32, i2c)

IP_self = "0.0.0.0"


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


if __name__ == '__main__':
    # 连接到 Wi-Fi， WIFI名称、密码
    Wifi_Name = 'LYLY'
    Wifi_Password = 'zyq20220701'
    connect_to_wifi(Wifi_Name, Wifi_Password)
    # 启动服务器
    start_server()






