from machine import Pin
import time

# 定义数码管各段的引脚
segments = [
    Pin(18, Pin.OUT),  # A
    Pin(19, Pin.OUT),  # B
    Pin(4, Pin.OUT),  # C
    Pin(2, Pin.OUT),  # D
    Pin(15, Pin.OUT),  # E
    Pin(5, Pin.OUT),  # F
    Pin(21, Pin.OUT),  # G
]

# 定义数字0-9的段码（共阳极）
digits = [
    (0,0,0,0,0,0,1),  # 0
    (1,0,0,1,1,1,1),  # 1
    (0,0,1,0,0,1,0),  # 2
    (0,0,0,0,1,1,0),  # 3
    (1,0,0,1,1,0,0),  # 4
    (0,1,0,0,1,0,0),  # 5
    (0,1,0,0,0,0,0),  # 6
    (0,0,0,1,1,1,1),  # 7
    (0,0,0,0,0,0,0),  # 8
    (0,0,0,0,1,0,0),  # 9
]

def display_digit(digit):
    for i in range(7):
        segments[i].value(digits[digit][i])

# 显示数字4
# display_digit(4)

# 循环显示1-9的数字
while True:
    for digit in range(1, 10):
        display_digit(digit)
        time.sleep(1)  # 每个数字显示1秒

# 保持显示
# while True:
#     time.sleep(1)
