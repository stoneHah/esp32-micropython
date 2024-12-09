from machine import Pin, I2S
import time

class AudioLoop:
    def __init__(self):
        # 配置麦克风(输入)
        self.audio_in = I2S(
            1,                      # I2S(1)用于输入
            sck=Pin(23),           # 麦克风SCK
            ws=Pin(22),            # 麦克风WS
            sd=Pin(21),            # 麦克风SD
            mode=I2S.RX,           # 接收模式
            bits=16,               # 采样位数
            format=I2S.MONO,       # 单声道
            rate=24000,            # 采样率
            ibuf=4096              # 输入缓冲区
        )
        
        # 配置扬声器(输出)
        self.audio_out = I2S(
            0,                      # I2S(0)用于输出
            sck=Pin(12),           # 扬声器SCK
            ws=Pin(14),            # 扬声器WS
            sd=Pin(13),            # 扬声器SD
            mode=I2S.TX,           # 发送模式
            bits=16,               # 采样位数
            format=I2S.MONO,       # 单声道
            rate=24000,            # 采样率
            ibuf=4096              # 输出缓冲区
        )
        
    def audio_loop(self):
        """从麦克风读取并实时播放"""
        # 创建音频缓冲区
        audio_buffer = bytearray(1024)
        
        print("开始音频循环...")
        try:
            while True:
                # 从麦克风读取数据
                num_read = self.audio_in.readinto(audio_buffer)
                print(f"读取到 {num_read} 字节数据")
                if num_read > 0:
                    # 直接写入扬声器
                    self.audio_out.write(audio_buffer[:num_read])
                    
        except KeyboardInterrupt:
            print("停止音频循环")
        finally:
            self.stop()
    
    def stop(self):
        """停止音频循环"""
        self.audio_in.deinit()
        self.audio_out.deinit()

# 使用示例
audio = AudioLoop()
audio.audio_loop() 