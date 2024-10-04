from machine import Pin, PWM
import time

# 创建PWM对象,连接到GPIO引脚(例如使用引脚15)
servo = PWM(Pin(12))

# 设置PWM频率为50Hz
servo.freq(50)

def set_angle(angle):
    # 将角度转换为占空比
    # SG90的脉冲宽度范围通常在0.5ms到2.5ms之间
    # 对应的占空比范围为2.5%到12.5%
    duty = int(((angle / 180) * 100 + 25) * 65535 / 1000)
    servo.duty_u16(duty)

set_angle(0)
# 主循环
# while True:
#     # 旋转到0度
#     set_angle(0)
#     time.sleep(1)
    
#     # 旋转到90度
#     set_angle(90)
#     time.sleep(1)
    
#     # 旋转到180度
#     set_angle(180)
#     time.sleep(1)