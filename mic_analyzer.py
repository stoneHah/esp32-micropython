 from machine import ADC, Pin
import time
import math

class MicrophoneAnalyzer:
    def __init__(self, pin=32, sample_window=50):
        self.adc = ADC(Pin(pin))
        # 设置11dB衰减，满量程电压为3.3V
        self.adc.atten(ADC.ATTN_11DB)
        # 设置读数位宽为12位(0-4095)
        self.adc.width(ADC.WIDTH_12BIT)
        self.sample_window = sample_window
    
    def get_sound_level(self):
        start_time = time.ticks_ms()
        sample_count = 0
        peak_to_peak = 0
        signal_max = 0
        signal_min = 4095  # ESP32的ADC是12位的，最大值是4095
        
        # 采样并找出峰峰值
        while (time.ticks_ms() - start_time) < self.sample_window:
            sample = self.adc.read()
            sample_count += 1
            
            if sample > signal_max:
                signal_max = sample
            elif sample < signal_min:
                signal_min = sample
                
        peak_to_peak = signal_max - signal_min
        # 转换为分贝值(近似值)
        # 添加一个小值避免log10(0)的错误
        db = 20 * math.log10(peak_to_peak + 1e-4)
        
        return {
            'peak_to_peak': peak_to_peak,
            'db': db,
            'samples': sample_count
        }

# 使用示例
if __name__ == '__main__':
    mic = MicrophoneAnalyzer()
    while True:
        result = mic.get_sound_level()
        print(f"分贝值: {result['db']:.1f}dB")
        print(f"峰峰值: {result['peak_to_peak']}")
        time.sleep(0.1)