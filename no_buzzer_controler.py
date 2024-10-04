from machine import Pin, PWM
import time

# 定义蜂鸣器引脚
buzzer = PWM(Pin(13))  # 假设蜂鸣器连接到GPIO 5

# 定义音符频率
notes = {
    'C4': 262,
    'D4': 294,
    'E4': 330,
    'F4': 349,
    'G4': 392,
    'A4': 440,
    'B4': 494,
    'C5': 523,
}

# 定义旋律
melody = ['C4', 'C4', 'G4', 'G4', 'A4', 'A4', 'G4', 
          'F4', 'F4', 'E4', 'E4', 'D4', 'D4', 'C4']

# 定义每个音符的持续时间（秒）
duration = 0.3

def play_tone(freq, duration):
    buzzer.freq(freq)
    buzzer.duty_u16(32768)  # 50% 占空比
    time.sleep(duration)
    buzzer.duty_u16(0)  # 停止发声
    time.sleep(0.05)  # 短暂停顿

def play_melody():
    for note in melody:
        play_tone(notes[note], duration)

print("开始播放")
# 播放旋律
play_melody() 
print("播放完毕")
# 清理
buzzer.deinit()