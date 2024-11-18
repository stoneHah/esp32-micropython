import socket
import time
from machine import Pin, I2S, Timer
import _thread

# 状态标志
STATE_IDLE = 0      # 空闲状态
STATE_RECORDING = 1 # 录音状态

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
        self.current_state = STATE_IDLE
        
        self.record_thread_running = True
        self.receive_thread_running = True
        self.play_thread_running = True
        
        # 按钮和LED配置
        self.button = Pin(0, Pin.IN, Pin.PULL_UP)  # 使用GPIO0作为按钮输入
        self.led = Pin(2, Pin.OUT)                 # 使用GPIO2作为LED指示
        
         # 定义特殊的结束标记
        self.END_MARKER = b'END_OF_AUDIO'
        
        # I2S麦克风配置
        self.audio_in = I2S(
            1,                      
            sck=Pin(23),           
            ws=Pin(22),            
            sd=Pin(21),            
            mode=I2S.RX,           
            bits=16,               
            format=I2S.MONO,       
            rate=16000,            
            ibuf=4096,
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
            ibuf=20000,
        )

        
    def send_audio(self, audio_buffer, num_read):
        try:
            # 分块发送音频数据
            audio_bytes = bytes(audio_buffer[:num_read])
            for i in range(0, num_read, self.chunk_size):
                chunk = audio_bytes[i:i + self.chunk_size]
                # 添加序号到数据包
                print(f"send_audio sequence: {self.sequence}")
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
        
    def start_recording(self):
        """开始录音并发送"""
        print("start_recording thread")
        audio_buffer = bytearray(self.audio_buffer_size)
        
        try:
            while self.record_thread_running:
                if self.current_state == STATE_RECORDING:
                    # 从麦克风读取数据
                    num_read = self.audio_in.readinto(audio_buffer)
                    if num_read > 0:
                        print(f"start_recording num_read: {num_read}")
                        self.send_audio(audio_buffer, num_read)
                
                time.sleep_ms(10)
        except Exception as e:
            print(f"录音线程错误: {e}")
        finally:
            print("录音线程结束")

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
    
    def stop_recording(self):
        """停止录音"""
        if self.current_state == STATE_RECORDING:
            # 先发送结束标记
            self.send_end_marker()
            # 然后更新状态
            self.current_state = STATE_IDLE
            self.sequence = 0
            print("录音已停止")
                
    def button_handler(self, pin):
        """按钮中断处理"""
        time.sleep(0.02)  # 消除按钮抖动
        print("button pressed, value:", pin.value())
        if pin.value() == 0:  # 按钮按下
            if self.current_state == STATE_IDLE:
                print("start recording...")
                self.current_state = STATE_RECORDING
            elif self.current_state == STATE_RECORDING:
                print("stop recording...")
                self.stop_recording()
                
    def cleanup(self):
        print("cleanup")
        self.current_state = STATE_IDLE
        self.record_thread_running = False
        self.receive_thread_running = False
        self.play_thread_running = False
        time.sleep_ms(200)  # 等待线程结束
        
        if self.sock:
            self.sock.close()
        if self.audio_in:
            self.audio_in.deinit()
        if self.audio_out:
            self.audio_out.deinit()
    
    def receive_audio(self):
        """接收并处理音频数据"""
        try:
            while self.receive_thread_running:
                # 处理接收
                try:
                    data, addr = self.sock.recvfrom(1500)
                    if data and len(data) >= 3:
                        message_type = data[0]
                        sequence = int.from_bytes(data[1:3], 'big')
                        audio_chunk = data[3:]
                        if message_type == 1:
                            self.audio_out.write(audio_chunk)
                except OSError as e:
                    if e.args[0] != 11:
                        print(f"接收错误: {e}")
                
                time.sleep_ms(1)
        except Exception as e:
            print(f"接收音频错误: {e}")
    
        
    
    
    def start_chat(self):
        """开始对话"""
        try:
            # 设置按钮中断
            self.button.irq(trigger=Pin.IRQ_FALLING, handler=self.button_handler)
            
            print("准备就绪，按下按钮开始/停止录音")

            # # 启动录音线程
            # _thread.start_new_thread(self.start_recording, ())
            
            # 启动接收线程
            _thread.start_new_thread(self.receive_audio, ())
            
            audio_buffer = bytearray(self.audio_buffer_size)
            # 主循环
            while True:
                if self.current_state == STATE_RECORDING:
                    # 从麦克风读取数据
                    num_read = self.audio_in.readinto(audio_buffer)
                    if num_read > 0:
                        print(f"start_recording num_read: {num_read}")
                        self.send_audio(audio_buffer, num_read)

                time.sleep_ms(1)
                
        except KeyboardInterrupt:
            print("end chat")
        finally:
            self.cleanup()
            
# AudioChatClient(host="192.168.0.109", port=8765).start_chat()
# AudioChatClient(host="192.168.2.227", port=8765).start_chat()
        
