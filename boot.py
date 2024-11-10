# boot.py -- run on boot-up

import network

def do_connect():
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect('TP-LINK_1301', 'Stone123')
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())

do_connect()