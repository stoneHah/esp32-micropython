from machine import ADC, Pin
import time

# ESP32的ADC引脚设置
# 可以使用GPIO32-GPIO39的ADC引脚
# ADC1通道(GPIO32-GPIO39)比ADC2更稳定
adc = ADC(Pin(32))  # 使用GPIO32作为ADC输入
# 设置11dB衰减，满量程电压为3.3V
adc.atten(ADC.ATTN_11DB)
# 设置读数位宽为12位(0-4095)
adc.width(ADC.WIDTH_12BIT)

def read_mic():
    while True:
        # 读取模拟值(0-4095)
        value = adc.read()
        # 将数值转换为电压值
        voltage = value * 3.3 / 4095
        print("Raw Value:", value, "Voltage:", voltage)
        time.sleep(0.1)

if __name__ == '__main__':
    read_mic() 