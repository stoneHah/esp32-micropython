import time
from machine import Pin, I2S, Timer
import json
import _thread
from uwebsockets import connect  # 使用正确的导入方式

# 首先需要安装websocket库
# 可以使用以下命令通过upip安装：
# import upip
# upip.install('micropython-websockets')

class AudioChatClient:
    def __init__(self):
        # 状态标志
        self.STATE_IDLE = 0      # 空闲状态
        self.STATE_RECORDING = 1 # 录音状态
        self.STATE_PLAYING = 2   # 播放状态
        self.current_state = self.STATE_IDLE
        
        # 按钮和LED配置
        self.button = Pin(0, Pin.IN, Pin.PULL_UP)  # 使用GPIO0作为按钮输入
        self.led = Pin(2, Pin.OUT)                 # 使用GPIO2作为LED指示
        
        # I2S麦克风配置
        self.audio_in = I2S(
            1,                      
            sck=Pin(23),           
            ws=Pin(22),            
            sd=Pin(21),            
            mode=I2S.RX,           
            bits=16,               
            format=I2S.MONO,       
            rate=8000,            
            ibuf=4096,
            # dma_buf_count=8,      # 增加DMA缓冲区数量
            # dma_buf_len=1024      # 设置DMA缓冲区长度
        )
        
        # I2S扬声器配置
        self.audio_out = I2S(
            0,                      
            sck=Pin(12),           
            ws=Pin(14),            
            sd=Pin(13),            
            mode=I2S.TX,           
            bits=16,               
            format=I2S.MONO,       
            rate=16000,            
            ibuf=4096,
            # dma_buf_count=8,
            # dma_buf_len=1024
        )
        
        # WebSocket配置
        self.ws = None
        self.ws_server = "ws://192.168.0.109:8000/ws"
        self.reconnect_attempts = 3
        self.is_connected = False
        
        # 音频缓冲区
        self.audio_buffer_size = 1024  # 保持4096字节以获得足够的检测窗口
        self.vad_window = []
        self.vad_window_size = 4  # 保持4个窗口
        self.vad_threshold = 200  # 降低阈值，使其更容易检测到声音
        self.frames_to_confirm_silence = 6  # 降低到8帧，约2秒静音就停止
        
        # 确保这些变量被正确初始化
        self.voice_frames = 0
        self.silence_frames = 0
        self.is_speaking = False
        
    def blink_led(self, times=1, interval=0.2):
        """LED闪烁指示"""
        for _ in range(times):
            self.led.value(1)
            time.sleep(interval)
            self.led.value(0)
            time.sleep(interval)
            
    def connect_websocket(self):
        """连接WebSocket服务器"""
        for attempt in range(self.reconnect_attempts):
            try:
                # 使用uwebsockets的connect函数创建连接
                self.ws = connect(self.ws_server)
                print("WebSocket连接成功")
                self.is_connected = True
                self.blink_led(2)  # 连接成功指示
                return True
            except Exception as e:
                print(f"WebSocket连接失败 (尝试 {attempt + 1}/{self.reconnect_attempts}): {e}")
                self.blink_led(5, 0.1)  # 错误指示
                time.sleep(2)
        return False
            
    def receive_messages(self):
        """接收服务器消息的线程"""
        while self.is_connected:
            try:
                # 使用uwebsockets的recv方法接收消息
                message = self.ws.recv()
                if not message:  # 连接关闭
                    self.is_connected = False
                    break
                    
                data = json.loads(message)
                
                if data['type'] == 'audio':
                    # 收到音频数据，播放
                    self.current_state = self.STATE_PLAYING
                    self.led.value(1)  # LED常亮表示播放中
                    self.play_audio(data['audio'])
                    self.led.value(0)
                    self.current_state = self.STATE_IDLE
                    
                elif data['type'] == 'text':
                    # 收到文本消息
                    print("AI回复:", data['text'])
                    
                elif data['type'] == 'status':
                    # 处理状态消息
                    print("状态:", data['message'])
                    
                elif data['type'] == 'error':
                    # 处理错误消息
                    print("错误:", data['message'])
                    self.blink_led(3, 0.1)
                    
            except Exception as e:
                print("接收消息错误:", e)
                self.is_connected = False
                break
                
    def detect_voice_activity(self, audio_data):
        """改进的语音活动检测"""
        try:
            # 计算当前帧的音量
            total = 0
            data_length = len(audio_data)  
            i = 0
            while i < data_length - 1:
                # 将两个字节组合成16位整数
                value = (audio_data[i+1] << 8) | audio_data[i]
                if value & 0x8000:
                    value -= 65536
                total += abs(value)
                i += 2
            
            current_average = total / (data_length // 2)
            
            # 更新滑动窗口
            self.vad_window.append(current_average)
            if len(self.vad_window) > self.vad_window_size:
                self.vad_window.pop(0)
            
            # 计算窗口平均值
            window_average = sum(self.vad_window) / len(self.vad_window)
            
            print(f"当前音量: {window_average:.2f}, 阈值: {self.vad_threshold}")
            
            # 声音检测逻辑
            if window_average > self.vad_threshold:
                self.voice_frames += 1
                self.silence_frames = 0
                if self.voice_frames > 2:
                    self.is_speaking = True
                    print("检测到说话")
            else:
                if self.is_speaking:  # 只在说话状态下计数静音帧
                    self.silence_frames += 1
                    print(f"静音帧数: {self.silence_frames}")
                self.voice_frames = 0
            
            # 静音检测
            if self.is_speaking and self.silence_frames >= self.frames_to_confirm_silence:
                print(f"检测到{self.frames_to_confirm_silence}帧静音，停止录音")
                return False
            
            return self.is_speaking
            
        except Exception as e:
            print(f"VAD错误: {e}")
            import sys
            sys.print_exception(e)
            return False
                
    def start_recording(self):
        """开始录音并发送"""
        self.current_state = self.STATE_RECORDING
        audio_buffer = bytearray(self.audio_buffer_size)
        
        # 重置VAD相关的计数器
        self.voice_frames = 0
        self.silence_frames = 0
        self.is_speaking = False
        self.vad_window = []
        
        while self.current_state == self.STATE_RECORDING:
            try:
                # 从麦克读取数据
                num_read = self.audio_in.readinto(audio_buffer)
                if num_read > 0:
                    print(f"发送数据块大小: {num_read} bytes")
                    
                    # 检测是否有声音活动
                    has_voice = self.detect_voice_activity(audio_buffer)
                    self.led.value(1 if has_voice else 0)  # LED指示
                    
                    # 确保WebSocket连接有效
                    if not self.is_connected:
                        print("WebSocket连接已断开，尝试重新连接...")
                        if not self.connect_websocket():
                            print("重连失败，停止录音")
                            self.stop_recording()
                            break
                    
                    try:
                        # 发送音频数据
                        message = {
                            'type': 'audio',
                            'audio': bytes(audio_buffer[:num_read]).hex()
                        }
                        self.ws.send(json.dumps(message))
                    except Exception as e:
                        print(f"发送数据错误: {e}")
                        self.is_connected = False
                        continue  # 继续循环，让重连机制工作
                    
                    # 如果已经开始说话且检测到足够长的静音，自动停止录音
                    if not has_voice and self.is_speaking:
                        print("检测到足够长的静音，自动停止录音")
                        self.stop_recording()
                        break
                    
            except Exception as e:
                print(f"录音错误: {e}")
                if "ECONNRESET" in str(e):
                    print("连接被重置，尝试重新连接...")
                    self.is_connected = False
                    if not self.connect_websocket():
                        print("重连失败，停止录音")
                        self.stop_recording()
                        break
                else:
                    break
                
    def stop_recording(self):
        """停止录音"""
        if self.current_state == self.STATE_RECORDING:
            self.current_state = self.STATE_IDLE
            # 发送录音结束信号
            if self.is_connected:
                try:
                    self.ws.send(json.dumps({
                        'type': 'end_recording'
                    }))
                except Exception as e:
                    print(f"发送结束信号失败: {e}")
                    self.is_connected = False
            
            # 重置所有状态
            self.voice_frames = 0
            self.silence_frames = 0
            self.is_speaking = False
            self.vad_window = []
            self.led.value(0)
            
    def play_audio(self, audio_data):
        """播放音频数据"""
        try:
            # 将hex字符串转换回字节
            audio_bytes = bytes.fromhex(audio_data)
            self.audio_out.write(audio_bytes)
        except Exception as e:
            print("播放错误:", e)
            
    def button_handler(self, pin):
        """按钮中断处理"""
        time.sleep(0.02)  # 消除按钮抖动
        if pin.value() == 0:  # 按钮按下
            if self.current_state == self.STATE_IDLE:
                print("开始录音...")
                _thread.start_new_thread(self.start_recording, ())
            elif self.current_state == self.STATE_RECORDING:
                print("停止录音...")
                self.stop_recording()
            
    def start_chat(self):
        """开始对话"""
        try:
            if not self.connect_websocket():
                print("无法连接到服务器")
                return
                
            # 启动接收消息的线程
            _thread.start_new_thread(self.receive_messages, ())
            
            # 设置按钮中断
            self.button.irq(trigger=Pin.IRQ_FALLING, handler=self.button_handler)
            
            print("准备就绪，按下按钮开始/停止录音")
            
            # 主循环保持运行
            while True:
                if not self.is_connected:
                    print("正在重新连接...")
                    if not self.connect_websocket():
                        break
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("结束对话")
        finally:
            self.cleanup()
            
    def cleanup(self):
        """清理资源"""
        self.current_state = self.STATE_IDLE
        self.is_connected = False
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
        self.audio_in.deinit()
        self.audio_out.deinit()
        self.led.value(0)

# 使用示例
# if __name__ == "__main__":
chat_client = AudioChatClient()
chat_client.start_chat()