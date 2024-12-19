from machine import Pin
import time

# 创建板载LED对象,ESP32-S3使用GPIO47作为板载LED引脚
led = Pin(47, Pin.OUT)

try:
    while True:
        # LED开启
        led.value(1)
        time.sleep(0.5)  # 延时0.5秒
        
        # LED关闭 
        led.value(0)
        time.sleep(0.5)  # 延时0.5秒
        
except KeyboardInterrupt:
    # 按Ctrl+C时关闭LED
    led.value(0)
