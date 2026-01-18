# RDK X5 USB WiFi (RTL8821CU) 共享热点配置指南

本文档记录了在 RDK X5 上使用 Realtek 8821CU USB WiFi 适配器构建局域网热点的配置过程。

## 1. 驱动安装
由于内核版本差异（6.1.83），需要手动指定内核源码路径进行编译：
```bash
cd ~/8821cu-20210916
make clean
make -j$(nproc) KSRC=/usr/src/linux-headers-6.1.83 KVER=6.1.83
sudo insmod 8821cu.ko
```
*注：USB 网卡识别后的接口名称通常为 `wlx90de80d368b3`。*

## 1.1 关键：处理 NetworkManager 冲突
在 RDK X5 (Ubuntu) 系统中，NetworkManager 默认会管理所有网卡，导致手动设置的静态 IP 被自动清除。**必须**将其设置为“托管之外”：

配置文件：`/etc/NetworkManager/conf.d/99-unmanage-rdk-ap.conf`
```ini
[keyfile]
unmanaged-devices=interface-name:wlx90de80d368b3
```
设置后执行 `sudo systemctl reload NetworkManager` 生效。

## 2. 热点配置 (hostapd)
配置文件路径：`/etc/hostapd/hostapd_rdk.conf`
内容如下：
```ini
interface=wlx90de80d368b3
driver=nl80211
ssid=RDK_AP_Hotspot
hw_mode=g
channel=6
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=rdk_wifi_888
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```

## 3. DHCP 服务配置 (dnsmasq)
配置文件路径：`/etc/dnsmasq_rdk.conf`
内容如下：
```ini
interface=wlx90de80d368b3
listen-address=192.168.50.1
bind-interfaces
dhcp-range=192.168.50.10,192.168.50.100,255.255.255.0,24h
domain=rdk.local
address=/rdk.local/192.168.50.1
```

## 4. 启动脚本/命令
为了实现开机自启，已创建 `/usr/local/bin/setup-rdk-ap.sh` 脚本并注册为 systemd 服务。

手动启动/测试命令：
```bash
sudo /usr/local/bin/setup-rdk-ap.sh
```

## 5. 开机自启配置 (Systemd)
已创建服务文件 `/etc/systemd/system/rdk-ap.service`：
```ini
[Unit]
Description=RDK X5 USB WiFi AP Startup Service
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/setup-rdk-ap.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

**启用命令**：
```bash
sudo systemctl daemon-reload
sudo systemctl enable rdk-ap.service
# 禁用自带的冲突服务
sudo systemctl disable hostapd dnsmasq
```

## 6. 管理命令
*   **查看连接设备**：`iw dev wlx90de80d368b3 station dump`
*   **查看服务状态**：`systemctl status rdk-ap.service`
*   **检查进程**：`ps aux | grep -E "hostapd|dnsmasq"`

## 7. 应用程序自启动配置
如果您需要前后端应用也随系统启动，请参考 [rdkx5自启服务配置.md](rdkx5自启服务配置.md)。

已配置的服务：
*   `camerahid-backend.service`: 后端 Flask 服务 (端口 5000)
*   `camerahid-frontend.service`: 前端 Vite 服务 (端口 5173)
