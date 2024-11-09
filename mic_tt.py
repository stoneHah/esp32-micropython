from machine import I2S, Pin

# 配置I2S接口
i2s = I2S(
    1,  # 使用I2S0
    sck=Pin(23),  # 时钟引脚
    ws=Pin(22),   # 词选择引脚
    sd=Pin(21),   # 数据引脚
    mode=I2S.RX,  # 接收模式
    bits=32,
    format=I2S.STEREO,
    rate=22050,
    ibuf=20000     # 缓冲区大小
)


# 创建一个缓冲区来存储音频数据
audio_buffer = bytearray(1024)

# 读取音频数据
while True:
    num_bytes_read = i2s.readinto(audio_buffer)
    # 处理音频数据
    print("Read {} bytes".format(num_bytes_read))