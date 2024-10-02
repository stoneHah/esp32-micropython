import max7219
from machine import Pin, SPI
import time

spi = SPI(1, baudrate=10000000, polarity=1, phase=0, sck=Pin(2), mosi=Pin(16))
ss = Pin(4, Pin.OUT)

display = max7219.Matrix8x8(spi, ss, 1)

def draw_arrow(x):
    display.fill(0)
    display.hline(x, 3, 6, 1)  # 水平线
    display.line(x+4, 1, x+6, 3, 1)  # 上斜线
    display.line(x+4, 5, x+6, 3, 1)  # 下斜线
    display.show()

while True:
    # 从左到右移动
    for x in range(-6, 8):
        draw_arrow(x)
        time.sleep(0.1)  # 暂停0.1秒
    
    # 短暂暂停
    time.sleep(0.5)
    
    # 清空显示
    display.fill(0)
    display.show()
    
    # 再次短暂暂停
    time.sleep(0.5)