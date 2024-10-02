# 读取DHT11温湿度传感器
import machine
import time
import dht

# 初始化DHT11传感器
dht11 = dht.DHT11(machine.Pin(15))

# 读取温湿度数据
def read_dht11():
    dht11.measure()
    temperature = dht11.temperature()
    humidity = dht11.humidity()
    return temperature, humidity

# 主函数
while True:
    temperature, humidity = read_dht11()
    print("温度: {:.2f}°C, 湿度: {:.2f}%".format(temperature, humidity))
    time.sleep(2)



