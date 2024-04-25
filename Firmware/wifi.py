def do_connect(ssid, pword):
    import network
    from machine import Pin
    import machine
    import utime
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        #print('connecting to network...')
        print(ssid)
        print(pword)
        #APS=list()
        #aps_near=sta_if.scan()
        #for AP in aps_near:         
        #    APS.append(AP[0].decode('utf-8'))         
        #if ssid in APS:           
            #print (APS)
        sta_if.active(True)
        sta_if.connect(ssid, pword)
        led = Pin(2, Pin.OUT)
        i=0
        while not sta_if.isconnected():
            led.on()
            utime.sleep_ms(100)
            led.off()
            utime.sleep_ms(100)
	    i=i+1
	    if i>10000 :
	    	machine.reset()
            pass
        print(sta_if.ifconfig())
        return 1
        
    else:
        print(sta_if.ifconfig())
        return 2
