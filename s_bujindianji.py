import machine
import time

# 定义步进电机引脚
IN1 = machine.Pin(15, machine.Pin.OUT)
IN2 = machine.Pin(2, machine.Pin.OUT)
IN3 = machine.Pin(4, machine.Pin.OUT)
IN4 = machine.Pin(5, machine.Pin.OUT)

# 定义步进序列
sequence = [
    [1,0,0,0],
    [0,1,0,0],
    [0,0,1,0],
    [0,0,0,1]
]

def step(direction):
    for step in range(4):
        for pin in range(4):
            if direction == 1:  # 顺时针
                [IN1, IN2, IN3, IN4][pin].value(sequence[step][pin])
            else:  # 逆时针
                [IN1, IN2, IN3, IN4][pin].value(sequence[3-step][pin])
        time.sleep_ms(3)  # 调整延迟以控制速度

def rotate(steps, direction):
    for _ in range(steps):
        step(direction)

# 示例使用
while True:
    print("顺时针旋转")
    rotate(512, 1)  # 顺时针旋转一周（假设步进电机为512步/圈）
    time.sleep(1)
    
    print("逆时针旋转")
    rotate(512, -1)  # 逆时针旋转一周
    time.sleep(1)
