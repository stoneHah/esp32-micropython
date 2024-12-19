import socket
import time
from machine import Pin, I2S, Timer
import uasyncio as asyncio
from myutil import RingBuffer

# 状态标志
STATE_STOPPED = 0      # 完全停止状态
STATE_STANDBY = 1     # 待机状态(可以录音和播放音频)
STATE_RECORDING = 2 # 录音状态
STATE_PLAYING = 3  # 播放状态

class AudioChatClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # 使用 UDP
        self.receive_buffer = bytearray(1500)  # 预分配接收缓冲区
        self.sock.setblocking(False)  # 设置非阻塞模式

        self.chunk_size = 1024  # UDP推荐的数据包大小
        self.sequence = 0  # 包序号，用于接收端重组
        self.audio_buffer_size = 1024
        self.current_state = STATE_STOPPED  # 初始状态为完全停止状态
        
        # 按钮和LED配置
        self.button = Pin(0, Pin.IN, Pin.PULL_UP)  # 保持GPIO0作为按钮输入，因为它通常用作BOOT按钮
        self.led = Pin(47, Pin.OUT)                # 修改为ESP32-S3板载LED的GPIO

        # 添加预缓冲区相关参数
        self.pre_buffer = []
        self.pre_buffer_size = 10  # 保存最近5帧的数据
        
         # 定义特殊的结束标记
        self.END_MARKER = b'END_OF_AUDIO'
        
         # VAD相关参数
        self.vad_threshold = 500  # 声音阈值，根据实际情况调整
        self.silence_frames = 0   # 连续静音帧计数
        self.voice_frames = 0     # 连续有声帧计数
        self.max_silence_frames = 50  # 最大静音帧数
        self.vad_window = []      # 滑动窗口
        self.vad_window_size = 4  # 窗口数量
        self.frames_to_confirm_silence = 50  # 降低到8帧，约2秒静音就停止
        
        self.is_speaking = False
        
        # I2S麦克风配置
        self.audio_in = I2S(
            1,                      
            sck=Pin(16),    # I2S_SCK (BCLK)        
            ws=Pin(15),     # I2S_WS (LRCK)
            sd=Pin(14),     # I2S_SD (DIN)
            mode=I2S.RX,           
            bits=16,               
            format=I2S.MONO,       
            rate=16000,            
            ibuf=4096,
        )

        # I2S扬声器配置
        self.audio_out = I2S(
            0,                      
            sck=Pin(17),    # I2S_SCK        
            ws=Pin(18),     # I2S_WS
            sd=Pin(19),     # I2S_SD
            mode=I2S.TX,           
            bits=16,               
            format=I2S.MONO,       
            rate=24000,            
            ibuf=20000,
        )

        self.playback_timeout = 800  # 800ms 超时时间
        self.last_playback_time = time.ticks_ms()
        
        # 添加事件循环相关属性
        self.loop = None
        self.tasks = []
        
        # 添加音频播放缓冲区
        self.play_buffer = RingBuffer(32000)  # 32KB 缓冲区
        self.min_playback_buffer = 4096  # 最小播放缓冲区大小
        
    def send_audio(self, audio_buffer, num_read):
        try:
            # 分块发送音频数据
            audio_bytes = bytes(audio_buffer[:num_read])
            for i in range(0, num_read, self.chunk_size):
                chunk = audio_bytes[i:i + self.chunk_size]
                # 添加序号到数据包
                # print(f"send_audio sequence: {self.sequence}")
                packet = self.sequence.to_bytes(2, 'big') + chunk
                self.sock.sendto(packet, (self.host, self.port))
                self.sequence = (self.sequence + 1) % 65536  # 循环使用序号
                time.sleep_ms(2)  # 短暂延迟
                
            return True
            
        except Exception as e:
            print(f"send_audio error: {e}")
            return False
            
    def close(self):
        try:
            if self.sock:
                self.sock.close()
                self.sock = None
        except:
            pass
        
    async def record_audio(self):
        """异步音频处理：处理录音和语音检测"""
        audio_buffer = bytearray(self.audio_buffer_size)
        
        while True:
            if self.current_state != STATE_STOPPED and self.current_state != STATE_PLAYING:
                try:
                    # 从麦克风读取数据
                    num_read = self.audio_in.readinto(audio_buffer)
                    if num_read > 0:
                        # 保存当前帧到预缓冲区
                        self.pre_buffer.append(audio_buffer[:num_read])
                        if len(self.pre_buffer) > self.pre_buffer_size:
                            self.pre_buffer.pop(0)
                            
                        has_voice = self.detect_voice(audio_buffer, num_read)
                        
                        # LED指示声音活动
                        self.led.value(1 if self.is_speaking else 0)
                        
                        if has_voice:
                            if self.current_state != STATE_RECORDING:
                                # 首次检测到声音，先发送预缓冲区的数据
                                print('发送预缓冲数据...')
                                for buffered_data in self.pre_buffer:
                                    self.send_audio(buffered_data, len(buffered_data))
                                self.current_state = STATE_RECORDING
                            
                            print('发送音频数据...')
                            self.send_audio(audio_buffer, num_read)
                        else:
                            if self.current_state == STATE_RECORDING:
                                print("检测到静音，停止发送")
                                self.current_state = STATE_STANDBY
                                print('发送结束标记...')
                                self.send_end_marker()
                                # 清空VAD窗口
                                self.vad_window.clear()
                except Exception as e:
                    print(f"音频处理错误: {e}")
            
            await asyncio.sleep_ms(10)

    def send_end_marker(self):
        """发送录音结束标记"""
        try:
            # 发送元数据包，标记结束
            end_metadata = {
                'type': 'end',
                'sequence_id': self.sequence
            }
            # 将元数据转换为字节并发送
            end_packet = self.END_MARKER
            self.sock.sendto(end_packet, (self.host, self.port))
            print("已发送录音结束标记")
            
        except Exception as e:
            print(f"发送结束标记错误: {e}")
    
    
                
    def button_handler(self, pin):
        """按钮中断处理"""
        time.sleep(0.02)  # 消除按钮抖动
        print("button pressed, value:", pin.value())
        if pin.value() == 0:  # 按钮按下
            if self.current_state == STATE_STOPPED:
                print("system startup, standby")
                self.current_state = STATE_STANDBY
                self.led.value(1)
            else:
                print("system shutdown")
                if self.current_state == STATE_RECORDING:
                    self.send_end_marker() #如果正在录音，则先发送结束标记
                self.current_state = STATE_STOPPED
                self.led.value(0)
                self.sequence = 0
                
    def cleanup(self):
        print("cleanup")
        self.current_state = STATE_STOPPED
        
        # 取消所有任务
        for task in self.tasks:
            task.cancel()
        
        if self.sock:
            self.sock.close()
        if self.audio_in:
            self.audio_in.deinit()
        if self.audio_out:
            self.audio_out.deinit()
    
    async def receive_audio(self):
        """异步接收并处理音频数据"""
        while True:
            try:
                try:
                    data, addr = self.sock.recvfrom(1500)
                    if data and len(data) >= 3:
                        message_type = data[0]
                        sequence = int.from_bytes(data[1:3], 'big')
                        audio_chunk = data[3:]
                        if message_type == 1:
                            # 将音频数据写入缓冲区
                            self.play_buffer.write(audio_chunk)
                            self.current_state = STATE_PLAYING
                            self.last_playback_time = time.ticks_ms()
                except OSError as e:
                    if e.args[0] != 11:  # EAGAIN
                        print(f"接收错误: {e}")
                
                # 检查播放超时
                if self.current_state == STATE_PLAYING and time.ticks_diff(time.ticks_ms(), self.last_playback_time) > self.playback_timeout:
                    self.current_state = STATE_STANDBY
                    
            except Exception as e:
                print(f"接收音频错误: {e}")
                
            await asyncio.sleep_ms(1)
            
    async def play_audio(self):
        """异步播放音频任务"""
        while True:
            if self.current_state == STATE_PLAYING:
                try:
                    # 当缓冲区数据足够或者有任何数据且超过播放超时时间时都进行播放
                    if (self.play_buffer.available >= self.min_playback_buffer or 
                        (self.play_buffer.available > 0 and 
                         time.ticks_diff(time.ticks_ms(), self.last_playback_time) > self.playback_timeout)):
                        
                        chunk = self.play_buffer.read(1024)  # 每次读取1024字节播放
                        if chunk:
                            self.audio_out.write(chunk)
                            self.last_playback_time = time.ticks_ms()
                except Exception as e:
                    print(f"播放音频错误: {e}")
            
            await asyncio.sleep_ms(5)
            
    def calculate_energy(self, buffer, length):
        """计算音频片段的能量"""
        energy = 0
        for i in range(0, length, 2):
            sample = buffer[i] | (buffer[i + 1] << 8)
            if sample & 0x8000:  # 处理负数
                sample = sample - 0x10000
            energy += abs(sample)
        return energy / (length // 2)
        
    def detect_voice(self, buffer, length):
        """使用滑动窗口检测声音活动"""
        try:
            # 计算当前帧的能量
            current_energy = self.calculate_energy(buffer, length)
            
            # 更新滑动窗口
            self.vad_window.append(current_energy)
            if len(self.vad_window) > self.vad_window_size:
                self.vad_window.pop(0)
                
            # 计算平均能量
            average_energy = sum(self.vad_window) / len(self.vad_window)
            
            # print(f"average_energy: {average_energy}, threshold: {self.vad_threshold}")
            
            # 判断是否有声音
            if average_energy > self.vad_threshold:
                self.voice_frames += 1
                self.silence_frames = 0
                if self.voice_frames >= 2:  # 至少需要2帧连续检测到声音
                    self.is_speaking = True
                    print("detected speaking...")
            else:
                if self.is_speaking:  # 只在说话状态下计数静音帧
                    self.silence_frames += 1
                    print(f"静音帧数: {self.silence_frames}")
                self.voice_frames = 0
                
            # 静音检测
            if self.is_speaking and self.silence_frames >= self.frames_to_confirm_silence:
                print(f"检测到{self.frames_to_confirm_silence}帧静音，停止录音")
                self.is_speaking = False
            
            return self.is_speaking
                
        except Exception as e:
            print(f"Voice detection error: {e}")
            self.is_speaking = False
            return self.is_speaking
    
    
    async def start_chat(self):
        """异步开始对话"""
        try:
            self.button.irq(trigger=Pin.IRQ_FALLING, handler=self.button_handler)
            
            print("准备就绪，按下按钮开始/停止录音")

            # 创建并启动任务
            record_task = asyncio.create_task(self.record_audio())
            receive_task = asyncio.create_task(self.receive_audio())
            play_task = asyncio.create_task(self.play_audio())  # 添加播放任务
            self.tasks = [record_task, receive_task, play_task]
            
            # 等待任务完成
            await asyncio.gather(*self.tasks)
                
        except Exception as e:
            print(f"聊天错误: {e}")
        finally:
            self.cleanup()
            
# AudioChatClient(host="192.168.0.109", port=8765).start_chat()
# AudioChatClient(host="192.168.2.227", port=8765).start_chat()
        
