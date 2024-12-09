import socket
from machine import Pin, I2S

class WAVPlayerClient:
    def __init__(self, server_ip, server_port, i2s_id=0, i2s_buffer_size=20480):
        self.server_ip = server_ip
        self.server_port = server_port

        # 配置 UDP 套接字
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(2)  # 设置超时时间，防止无限等待

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
        print(f"客户端已启动，准备接收来自 {server_ip}:{server_port} 的音频数据")

    def receive_and_play(self):
        """接收音频数据并播放"""
        self.sock.sendto(b'START', (self.server_ip, self.server_port))
        print("等待音频数据...")
        while True:
            try:
                data, addr = self.sock.recvfrom(1500)  # 接收最大 1024 字节数据包

                # 检查是否收到结束信号
                if data == b'END':
                    print("接收到音频结束信号")
                    break

                chunk = data[1:]

                # 将数据写入 I2S 进行播放
                bytes_written = self.audio_out.write(chunk)
                if bytes_written != len(chunk):
                    print(f"写入数据不完整，期望 {len(data)} 字节，实际 {bytes_written} 字节")
            except socket.timeout:
                print("等待数据超时...")
            except Exception as e:
                print(f"接收或播放时发生错误: {e}")
                break


    def close(self):
        """释放资源"""
        self.audio_out.deinit()
        self.sock.close()
        print("客户端已关闭")

wav_player = WAVPlayerClient('192.168.0.109', 8632)
wav_player.receive_and_play()
