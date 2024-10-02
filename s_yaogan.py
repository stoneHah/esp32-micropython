from machine import ADC, Pin
import time

# 创建两个ADC对象,分别对应X轴和Y轴
adc_x = ADC(Pin(32))
adc_y = ADC(Pin(33))

# 设置ADC的衰减,以扩大测量范围
adc_x.atten(ADC.ATTN_11DB)
adc_y.atten(ADC.ATTN_11DB)

btn = Pin(18, Pin.IN, Pin.PULL_UP)


while True:
    # 读取X轴和Y轴的ADC值
    x_value = adc_x.read()
    y_value = adc_y.read()
    
    # 将ADC值映射到-100到100的范围
    x_mapped = (x_value - 2048) / 20.48
    y_mapped = (y_value - 2048) / 20.48
    
    print(f"X: {x_mapped:.2f}, Y: {y_mapped:.2f}, btn: {btn.value()}")
    
    time.sleep(0.1)  # 每0.1秒读取一次数据
