from machine import UART,SPI,Pin
from ST7735 import TFT
from font import sysfont, seriffont, terminalfont
import time
import math

# Fiz pra testar 2 displays com o mesmo script pq sim.
display085 = True

# pins: sck 6, tx/mosi 7, mosi/dc 15, rst 14, cs 5.
TFT_CLK =   const(18)
TFT_MOSI =  const(23)
TFT_DC =    const(2)
TFT_RST =   const(4)
TFT_CS =    const(5)

# 20 Mhz = 20_000_000 (default), 51_200_000, 80_000_000
spi = SPI(2, baudrate=80_000_000, polarity=0, phase=0, bits=8, sck=Pin(TFT_CLK), mosi=Pin(TFT_MOSI), miso=None)

tft = TFT(spi, TFT_DC, TFT_RST, TFT_CS)

# Na vdd, no Aliexpress dizia que o display 0.85' (ST7735) era 128x160, mas
# depois desses testes confirmei ser na verdade 128x128.
if (display085):
    tft.initb2() # lcd 0.85'
    tft.invertcolor(True)
    tft.rgb(False)
else:
    tft.initg() # lcd 1.77' 128x160

tft.rotation(2);

print('Hello from Pi Pico using Python. Running: Display SPI ST7735.')

def testlines(color):
    tft.fill(TFT.BLACK)
    for x in range(0, tft.size()[0], 6):
        tft.line((0,0),(x, tft.size()[1] - 1), color)
    for y in range(0, tft.size()[1], 6):
        tft.line((0,0),(tft.size()[0] - 1, y), color)

    tft.fill(TFT.BLACK)
    for x in range(0, tft.size()[0], 6):
        tft.line((tft.size()[0] - 1, 0), (x, tft.size()[1] - 1), color)
    for y in range(0, tft.size()[1], 6):
        tft.line((tft.size()[0] - 1, 0), (0, y), color)

    tft.fill(TFT.BLACK)
    for x in range(0, tft.size()[0], 6):
        tft.line((0, tft.size()[1] - 1), (x, 0), color)
    for y in range(0, tft.size()[1], 6):
        tft.line((0, tft.size()[1] - 1), (tft.size()[0] - 1,y), color)

    tft.fill(TFT.BLACK)
    for x in range(0, tft.size()[0], 6):
        tft.line((tft.size()[0] - 1, tft.size()[1] - 1), (x, 0), color)
    for y in range(0, tft.size()[1], 6):
        tft.line((tft.size()[0] - 1, tft.size()[1] - 1), (0, y), color)

def testfastlines(color1, color2):
    tft.fill(TFT.BLACK)
    for y in range(0, tft.size()[1], 5):
        tft.hline((0,y), tft.size()[0], color1)
    for x in range(0, tft.size()[0], 5):
        tft.vline((x,0), tft.size()[1], color2)

def testdrawrects(color):
    tft.fill(TFT.BLACK);
    for x in range(0,tft.size()[0],6):
        tft.rect((tft.size()[0]//2 - x//2, tft.size()[1]//2 - x/2), (x, x), color)

def testfillrects(color1, color2):
    tft.fill(TFT.BLACK);
    for x in range(tft.size()[0],0,-6):
        tft.fillrect((tft.size()[0]//2 - x//2, tft.size()[1]//2 - x/2), (x, x), color1)
        tft.rect((tft.size()[0]//2 - x//2, tft.size()[1]//2 - x/2), (x, x), color2)


def testfillcircles(radius, color):
    for x in range(radius, tft.size()[0], radius * 2):
        for y in range(radius, tft.size()[1], radius * 2):
            tft.fillcircle((x, y), radius, color)

def testdrawcircles(radius, color):
    for x in range(0, tft.size()[0] + radius, radius * 2):
        for y in range(0, tft.size()[1] + radius, radius * 2):
            tft.circle((x, y), radius, color)

def testtriangles():
    tft.fill(TFT.BLACK);
    color = 0xF800
    w = tft.size()[0] // 2
    x = tft.size()[1] - 1
    y = 0
    z = tft.size()[0]
    for t in range(0, 15):
        tft.line((w, y), (y, x), color)
        tft.line((y, x), (z, x), color)
        tft.line((z, x), (w, y), color)
        x -= 4
        y += 4
        z -= 4
        color += 100

def testroundrects():
    tft.fill(TFT.BLACK);
    color = 100
    for t in range(5):
        x = 0
        y = 0
        w = tft.size()[0] - 2
        h = tft.size()[1] - 2
        for i in range(17):
            tft.rect((x, y), (w, h), color)
            x += 2
            y += 3
            w -= 4
            h -= 6
            color += 1100
        color += 100

def tftprinttest():
    tft.fill(TFT.BLACK);
    v = 30
    tft.text((0, v), "Hello World!", TFT.RED, sysfont, 1, nowrap=True)
    v += sysfont["Height"]
    tft.text((0, v), "Hello World!", TFT.YELLOW, sysfont, 2, nowrap=True)
    v += sysfont["Height"] * 2
    tft.text((0, v), "Hello World!", TFT.GREEN, sysfont, 3, nowrap=True)
    v += sysfont["Height"] * 3
    tft.text((0, v), str(1234.567), TFT.BLUE, sysfont, 4, nowrap=True)
    time.sleep_ms(2000)
    tft.fill(TFT.BLACK);
    v = 0
    tft.text((0, v), "Hello World!", TFT.RED, sysfont)
    v += sysfont["Height"]
    tft.text((0, v), str(math.pi), TFT.GREEN, sysfont)
    v += sysfont["Height"]
    tft.text((0, v), " Want pi?", TFT.GREEN, sysfont)
    v += sysfont["Height"] * 2
    tft.text((0, v), hex(8675309), TFT.GREEN, sysfont)
    v += sysfont["Height"]
    tft.text((0, v), " Print HEX!", TFT.GREEN, sysfont)
    v += sysfont["Height"] * 2
    tft.text((0, v), "Sketch has been", TFT.WHITE, sysfont)
    v += sysfont["Height"]
    tft.text((0, v), "running for: ", TFT.WHITE, sysfont)
    v += sysfont["Height"]
    tft.text((0, v), str(time.ticks_ms() / 1000), TFT.PURPLE, sysfont)
    v += sysfont["Height"]
    tft.text((0, v), " seconds.", TFT.WHITE, sysfont)

def test_main():
    tft.fill(TFT.BLACK)
    tft.text((0, 0), "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur adipiscing ante sed nibh tincidunt feugiat. Maecenas enim massa, fringilla sed malesuada et, malesuada sit amet turpis. Sed porttitor neque ut ante pretium vitae malesuada nunc bibendum. Nullam aliquet ultrices massa eu hendrerit. Ut sed nisi lorem. In vestibulum purus a tortor imperdiet posuere. ", TFT.WHITE, sysfont, 1)
    time.sleep_ms(1000)

    tftprinttest()
    time.sleep_ms(4000)

    testlines(TFT.YELLOW)
    time.sleep_ms(500)

    testfastlines(TFT.RED, TFT.BLUE)
    time.sleep_ms(500)

    testdrawrects(TFT.GREEN)
    time.sleep_ms(500)

    testfillrects(TFT.YELLOW, TFT.PURPLE)
    time.sleep_ms(500)

    tft.fill(TFT.BLACK)
    testfillcircles(10, TFT.BLUE)
    testdrawcircles(10, TFT.WHITE)
    time.sleep_ms(500)

    testroundrects()
    time.sleep_ms(500)

    testtriangles()
    time.sleep_ms(1000)

    while (True):
        test()

def printhello():
    x = 0
    y = 0
    message = "Hello World"
    fontSize = 2
    fontType = sysfont # sysfont (the best), terminalfont, seriffont
    tft.text((x, y), message, TFT.GRAY, fontType, fontSize) # 1
    tft.text((x, y+15), message, TFT.MAROON, fontType, fontSize)
    tft.text((x, y+30), message, TFT.GRAY, fontType, fontSize)
    tft.text((x, y+45), message, TFT.MAROON, fontType, fontSize)
    tft.text((x, y+60), message, TFT.GRAY, fontType, fontSize) # 5
    tft.text((x, y+75), message, TFT.MAROON, fontType, fontSize)
    tft.text((x, y+90), message, TFT.GRAY, fontType, fontSize) # 7 (retrato 128x128)
    tft.text((x, y+105), message, TFT.MAROON, fontType, fontSize) # 8 (paisagem 128x160, retrato 128x128)
    tft.text((x, y+120), message, TFT.GRAY, fontType, fontSize) # 9 (metade fora do frame 128x128)
    tft.text((x, y+135), message, TFT.MAROON, fontType, fontSize) # 10 (retrato 128x160)
    tft.text((x, y+150), message, TFT.NAVY, fontType, fontSize) # 11 (metade fora do frame 128x160)

def test():
    while (True):
        tft.fill(TFT.BLACK)
        printhello()
        time.sleep_ms(1000)

        tft.fill(TFT.RED)
        printhello()
        time.sleep_ms(1000)

        tft.fill(TFT.GREEN)
        printhello()
        time.sleep_ms(1000)

        tft.fill(TFT.BLUE)
        printhello()
        time.sleep_ms(1000)

        tft.fill(TFT.YELLOW)
        printhello()
        time.sleep_ms(1000)

        tft.fill(TFT.PURPLE)
        printhello()
        time.sleep_ms(1000)

        tft.fill(TFT.WHITE)
        printhello()
        time.sleep_ms(1000)


test()
#test_main()
