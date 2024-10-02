import machine
import time

led = machine.Pin(2, machine.Pin.OUT)

while True:
    led.value(not led.value())
    print("ON" if led.value() else "OFF")
    time.sleep(1)