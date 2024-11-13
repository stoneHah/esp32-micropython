import time
from machine import Pin, I2S, Timer
import json
import _thread
from uwebsockets import connect  # 使用正确的导入方式

# 首先需要安装websocket库
# 可以使用以下命令通过upip安装：
# import upip
# upip.install('micropython-websockets')

class RingBuffer:
    """环形缓冲区实现"""
    def __init__(self, size):
        self.size = size
        self.buffer = bytearray(size)
        self.write_pos = 0
        self.read_pos = 0
        self.available = 0
        
    def write(self, data):
        """写入数据到缓冲区"""
        print(f"写入数据到缓冲区")
        data_len = len(data)
        
        # 检查是否有足够的空间写入数据
        if data_len > self.size - self.available:
            print("缓冲区空间不足")
            return 0
            
        # 计算第一段可写入长度，需要考虑read_pos的位置
        if self.write_pos >= self.read_pos:
            # 写指针在读指针后面，需要考虑到缓冲区末尾的空间
            first_part = min(data_len, self.size - self.write_pos)
        else:
            # 写指针在读指针前面，只能写到读指针位置
            first_part = min(data_len, self.read_pos - self.write_pos)
            
        # 写入第一部分
        self.buffer[self.write_pos:self.write_pos + first_part] = data[:first_part]
        
        if first_part < data_len:
            # 需要环绕写入时，确保不会覆盖未读取的数据
            second_part = data_len - first_part
            if self.read_pos < second_part:
                print("环绕写入时空间不足")
                return first_part  # 只返回成功写入的部分
                
            self.buffer[0:second_part] = data[first_part:]
            self.write_pos = second_part
        else:
            self.write_pos = (self.write_pos + first_part) % self.size
            
        self.available += data_len
        print(f"写入数据后，缓冲区可用大小: {self.available}")
        return data_len
        
    def read(self, size):
        """从缓冲区读取数据"""
        print(f"从缓冲区读取数据")
        if self.available == 0:
            return bytearray(0)
            
        read_size = min(size, self.available)
        first_part = min(read_size, self.size - self.read_pos)
        result = bytearray(read_size)
        
        result[:first_part] = self.buffer[self.read_pos:self.read_pos + first_part]
        
        if first_part < read_size:
            # 需要环绕读取
            print(f"需要环绕读取")
            second_part = read_size - first_part
            result[first_part:] = self.buffer[0:second_part]
            self.read_pos = second_part
        else:
            print(f"不需要环绕读取")
            self.read_pos = (self.read_pos + first_part) % self.size
            
        self.available -= read_size
        return result

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
            rate=24000,            
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
        
        # 音频播放缓冲区
        self.play_buffer = RingBuffer(1024 * 8)  # 8KB的环形缓冲区
        self.play_chunk_size = 1024  # 每次播放1KB
        self._is_playing = False
        self._player_thread_running = False
        
        # 在初始化时就启动播放线程
        # self._start_player_thread()
        
        self._ws_monitor_running = False
        self._last_ws_check = time.time()
        self.ws_check_interval = 5  # 每5秒检查一次连接状态
        
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
                if message is None:  # 检查是否接收到None
                    print("未接收到消息，可能是暂时没有数据")
                    continue
                    
                data = json.loads(message)
                
                if data['type'] == 'audio':
                    print("收到音频数据")  # 减少打印数据量
                    # 不要直接播放，而是写入缓冲区
                    audio_bytes = bytes.fromhex(data['audio'])
                    self.audio_out.write(audio_bytes)
                    # self.play_audio(audio_bytes)  # 使用缓冲区机制
                    
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
                import sys
                sys.print_exception(e)  # 打印详细错误信息
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
                    
                    # 发送音频数据 - 不再在这里处理连接状态
                    if self.is_connected:
                        try:
                            message = {
                                'type': 'audio',
                                'audio': bytes(audio_buffer[:num_read]).hex()
                            }
                            self.ws.send(json.dumps(message))
                        except Exception as e:
                            print(f"发送数据错误: {e}")
                            self.is_connected = False
                    
                    # 如果已经开始说话且检测到足够长的静音，自动停止录音
                    if not has_voice and self.is_speaking:
                        print("检测到足够长的静音，自动停止录音")
                        self.stop_recording()
                        break
                    
            except Exception as e:
                print(f"录音错误: {e}")
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
            
    def start_audio_player(self):
        """开始播放音频"""
        self._is_playing = True
        
    def stop_audio_player(self):
        """停止当前音频的播放"""
        self._is_playing = False
        
    def _audio_player_thread(self):
        """音频播放线程"""
        print("+++++++++++++++播放线程开始运行")
        while self._player_thread_running:
            if self._is_playing and self.play_buffer.available > 0:
                try:
                    chunk_size = min(self.play_chunk_size, self.play_buffer.available)
                    chunk = self.play_buffer.read(chunk_size)
                    self.audio_out.write(chunk)
                except Exception as e:
                    print("播放线程错误:", e)
            else:
                time.sleep_ms(10)  # 减少等待时间
                
    def play_audio(self, audio_bytes):
        """处理接收到的音频数据"""
        try:
            # 写入环形缓冲区
            while len(audio_bytes) > 0:
                written = self.play_buffer.write(audio_bytes)
                if written == 0:
                    # 缓冲区满，等待一会
                    time.sleep_ms(20)
                else:
                    audio_bytes = audio_bytes[written:]
            
            # 开始播放
            self.start_audio_player()
                
        except Exception as e:
            print("音频处理错误:", e)
            
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
            
    def monitor_websocket(self):
        """WebSocket连接监控线程"""
        print("开始WebSocket监控")
        self._ws_monitor_running = True
        
        while self._ws_monitor_running:
            try:
                current_time = time.time()
                if not self.is_connected and (current_time - self._last_ws_check) >= self.ws_check_interval:
                    print("检测到WebSocket断开，尝试重连...")
                    if self.connect_websocket():
                        print("WebSocket重连成功")
                    else:
                        print("WebSocket重连失败")
                    self._last_ws_check = current_time
                    
                time.sleep(1)
            except Exception as e:
                print(f"WebSocket监控错误: {e}")
                time.sleep(1)

    def start_chat(self):
        """开始对话"""
        try:
            # 初始连接
            if not self.connect_websocket():
                print("无法连接到服务器")
                return
                
            # 启动WebSocket监控线程
            _thread.start_new_thread(self.monitor_websocket, ())
            
            # 启动接收消息的线程
            _thread.start_new_thread(self.receive_messages, ())
            
            # 设置按钮中断
            self.button.irq(trigger=Pin.IRQ_FALLING, handler=self.button_handler)
            
            print("准备就绪，按下按钮开始/停止录音")
            
            # 主循环
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("结束对话")
        finally:
            self.cleanup()
            
    def cleanup(self):
        """清理资源"""
        self._ws_monitor_running = False  # 停止WebSocket监控
        self.current_state = self.STATE_IDLE
        self.is_connected = False
        self._player_thread_running = False
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
        self.audio_in.deinit()
        self.audio_out.deinit()
        self.led.value(0)

    def _start_player_thread(self):
        """启动音频播放线程"""
        self._player_thread_running = True
        _thread.start_new_thread(self._audio_player_thread, ())

# 使用示例
# if __name__ == "__main__":
chat_client = AudioChatClient()
chat_client.start_chat()