from machine import ADC, Pin, SPI
import time
import max7219

# 创建两个ADC对象,分别对应X轴和Y轴
adc_x = ADC(Pin(32))
adc_y = ADC(Pin(33))

# 设置ADC的衰减,以扩大测量范围
adc_x.atten(ADC.ATTN_11DB)
adc_y.atten(ADC.ATTN_11DB)

btn = Pin(18, Pin.IN, Pin.PULL_UP)

# 初始化SPI和MAX7219
spi = SPI(1, baudrate=10000000, polarity=1, phase=0, sck=Pin(2), mosi=Pin(16))
ss = Pin(4, Pin.OUT)

display = max7219.Matrix8x8(spi, ss, 1)
# spi = SPI(1, baudrate=10000000, polarity=0, phase=0)
# cs = Pin(4, Pin.OUT)
# display = max7219.Matrix8x8(spi, cs, 1)  # 假设使用1个8x8点阵


while True:
    # 读取X轴和Y轴的ADC值
    x_value = adc_x.read()
    y_value = adc_y.read()
    
    # 将ADC值映射到0到7的范围（适合8x8点阵）
    x_mapped = min(7, max(0, int((x_value - 0) * 8 / 4095)))
    y_mapped = min(7, max(0, int((y_value - 0) * 8 / 4095)))
    
    print(f"X: {x_mapped}, Y: {y_mapped}, btn: {btn.value()}")
    
    # 清除显示
    display.fill(0)
    # 在点阵上显示点
    display.pixel(x_mapped, y_mapped, 1)
    # 更新显示
    display.show()
    
    time.sleep(0.1)  # 每0.1秒读取一次数据
