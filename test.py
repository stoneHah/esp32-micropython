import machine
import st7789.st7789py as st7789
import time

# 降低SPI频率
spi = machine.SPI(2, baudrate=26000000, polarity=1, phase=0, sck=machine.Pin(18), mosi=machine.Pin(23))
dc = machine.Pin(2, machine.Pin.OUT)
rst = machine.Pin(4, machine.Pin.OUT)
cs = machine.Pin(5, machine.Pin.OUT)

# 创建显示对象，移除rotation参数
display = st7789.ST7789(
    spi,
    240,
    240,
    reset=rst,
    dc=dc,
    cs=cs)

# 清屏为白色
display.fill(st7789.WHITE)

# 显示一些文本
display.text("你好，世界！", 10, 10, st7789.BLACK)
display.text("ESP32 + ST7789", 10, 30, st7789.RED)
display.text("0.96英寸 IPS", 10, 50, st7789.BLUE)

# 刷新显示
display.show()

# 等待5秒
time.sleep(5)

# 显示一些图形
display.fill(st7789.BLACK)
display.fill_rect(20, 20, 200, 158, st7789.RED)
display.fill_rect(40, 40, 160, 118, st7789.GREEN)
display.fill_rect(60, 60, 120, 78, st7789.BLUE)

# 刷新显示
display.show()