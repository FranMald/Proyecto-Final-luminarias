def do_connect(ssid, pword):
    import network
    from machine import Pin
    import utime
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        print(ssid)
        print(pword)
        APS=list()
        aps_near=sta_if.scan()
        for AP in aps_near:         
            APS.append(AP[0].decode('utf-8'))         
        if ssid in APS:           
            print (APS)
            sta_if.active(True)
            sta_if.connect(ssid, pword)
            led = Pin(2, Pin.OUT)
            while not sta_if.isconnected():
                led.on()
                utime.sleep_ms(100)
                led.off()
                utime.sleep_ms(100)
                pass
            print('network config:', sta_if.ifconfig())
            return 1
        else:
            print("ssid no encoontrada")
            return 0
    else:
        print('network config:', sta_if.ifconfig())
        return 2
	
	'+IDEUPcontent+'