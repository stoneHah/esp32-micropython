from audio_boardcast import AudioChatClient
import uasyncio as asyncio

# 启动方式改为：
async def main():
    client = AudioChatClient(host="192.168.0.109", port=8765)
    # client = AudioChatClient(host="192.168.2.227", port=8765)
    await client.start_chat()

asyncio.run(main())