# 开启无线热点
import network

def start_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid='ESP32-AP', password='12345678')

    # 设置其他参数
    ap.config(authmode=network.AUTH_WPA_WPA2_PSK)
    ap.config(max_clients=10)

    print('无线热点已开启')
    print('SSID:', ap.config('essid'))
    # print('密码:', ap.config('password'))
    print('IP地址:', ap.ifconfig()[0]) 

start_ap()

