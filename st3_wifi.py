import network

def do_connect():
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect('TP-LINK_1301', 'Stone123')
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())

def listen_for_commands():
    import socket
    from machine import Pin

    led = Pin(2, Pin.OUT)  # 假设LED连接到GPIO 2
    addr = ('0.0.0.0', 12345)  # 监听所有IP，端口21818
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(addr)

    print('正在监听UDP命令...')
    while True:
        data, addr = s.recvfrom(1024)
        command = data.decode('utf-8').strip().lower()
        
        if command == 'light on':
            led.on()
            print('LED已开启')
        elif command == 'light off':
            led.off()
            print('LED已关闭')
        else:
            print('未知命令:', command)

do_connect()
# listen_for_commands()


