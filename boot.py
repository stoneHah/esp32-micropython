# boot.py -- run on boot-up

import network

def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect('LXZH', 'lxzh1234')
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())

do_connect()