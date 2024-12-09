# Complete project details at https://RandomNerdTutorials.com

import wifimgr
from time import sleep
import machine

try:
  import usocket as socket
except:
  import socket

led = machine.Pin(2, machine.Pin.OUT)

wlan = wifimgr.get_connection()
if wlan is None:
    print("Could not initialize the network connection.")
    while True:
        pass  # you shall not pass :D

# Main Code goes here, wlan is a working network.WLAN(STA_IF) instance.
print("ESP OK")

from audio_boardcast import AudioChatClient
import uasyncio as asyncio

# 启动方式改为：
async def main():
    client = AudioChatClient(host="139.196.110.71", port=8765)
    # client = AudioChatClient(host="192.168.2.227", port=8765)
    await client.start_chat()

asyncio.run(main())