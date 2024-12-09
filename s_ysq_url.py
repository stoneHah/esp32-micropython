import urequests
from machine import Pin, I2S
import os

class B525Player:
    def __init__(self, sck_pin=12, ws_pin=14, sd_pin=13):
        """初始化B525音频播放器
        Args:
            sck_pin: I2S时钟引脚
            ws_pin: I2S字选择引脚  
            sd_pin: I2S数据引脚
        """
        # 配置I2S接口
        self.audio_out = I2S(
            0,                          # I2S ID
            sck=Pin(sck_pin),          # 串行时钟
            ws=Pin(ws_pin),            # 字选择
            sd=Pin(sd_pin),            # 串行数据
            mode=I2S.TX,               # 发送模式
            bits=16,                   # 采样位数
            format=I2S.MONO,         # 立体声
            rate=44100,                # 采样率
            ibuf=20000                 # 内部缓冲区大小
        )
        
    def play_from_url(self, url):
        """从URL播放WAV音频文件
        Args:
            url: WAV文件的URL地址
        """
        try:
            # 发起HTTP请求
            response = urequests.get(url, stream=True)
            if response.status_code != 200:
                print("HTTP请求错误:", response.status_code)
                return

            # 跳过WAV文件头(44字节)
            for _ in range(44):
                response.raw.read(1)
            
            # 读取并播放音频数据
            while True:
                # 从URL读取音频数据
                chunk = response.raw.read(1024)
                if not chunk:
                    break
                
                # 直接通过I2S接口发送数据
                num_written = 0
                while num_written < len(chunk):
                    num_written += self.audio_out.write(chunk[num_written:])
            
            response.close()
                        
        except Exception as e:
            print("播放错误:", e)
            
    def stop(self):
        """停止播放"""
        self.audio_out.deinit()
        
# 使用示例:
player = B525Player()

# 从URL播放WAV文件
player.play_from_url('http://192.168.0.109/audio_f/aa.wav')  # WAV文件需要是16位立体声、44.1kHz格式
player.stop()

