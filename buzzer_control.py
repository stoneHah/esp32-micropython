from machine import Pin
import time

# 设置蜂鸣器连接的GPIO引脚
BUZZER_PIN = 13

# 创建蜂鸣器对象
buzzer = Pin(BUZZER_PIN, Pin.OUT)

def beep(duration):
    """
    控制蜂鸣器发声
    :param duration: 发声持续时间(秒)
    """
    buzzer.on()
    time.sleep(duration)
    buzzer.off()

try:
    while True:
        # 蜂鸣器响0.5秒
        beep(0.5)
        # 暂停1秒
        time.sleep(1)

except KeyboardInterrupt:
    # 当按下Ctrl+C时,清理引脚设置并退出
    buzzer.off()
    print("程序已退出")