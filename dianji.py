import machine
import time

# 初始化GPIO 12作为输出引脚
motor_pin = machine.Pin(26, machine.Pin.OUT)

# 主循环
while True:
    print("打开电机")
    motor_pin.value(1) # 或使用 motor_pin.value(1)
    time.sleep(5)

    print("关闭电机")
    motor_pin.value(0)  # 或使用 motor_pin.value(0)
    time.sleep(1)


