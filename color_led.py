from machine import Pin
from neopixel import NeoPixel
import time
import random

# 创建NeoPixel对象
pin = Pin(48, Pin.OUT)   
np = NeoPixel(pin, 1)    

def random_color():
    # 生成随机的RGB值
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return (r, g, b)

try:
    while True:
        # 设置随机颜色
        color = random_color()
        np[0] = color
        np.write()
        
        # 打印当前RGB值
        print(f"RGB: {color}")
        
        # 延时1秒
        time.sleep(1)
        
except KeyboardInterrupt:
    # 按Ctrl+C时关闭LED
    np[0] = (0, 0, 0)
    np.write()
