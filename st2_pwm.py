import machine
import time

print("st2_pwm")
pwm_pin = machine.Pin(2, machine.Pin.OUT)
pwm = machine.PWM(pwm_pin, freq=1000)

while True:
    for duty in range(0, 1024, 10):
        pwm.duty(duty)
        time.sleep(0.01)
    for duty in range(1023, -1, -10):
        pwm.duty(duty)
        time.sleep(0.01)
