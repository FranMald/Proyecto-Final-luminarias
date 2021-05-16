def do_connect():
    import network
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        #sta_if.connect('panchoAP','nodemcu121')
        sta_if.connect('Fibertel WiFi621 2.4GHz', '00437348258')
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())
