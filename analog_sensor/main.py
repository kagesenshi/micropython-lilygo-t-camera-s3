import machine
import ssd1306
import time
import network
import urequests
import errno

config = {}
with open('config.ini') as cfile:
    for l in cfile:
        l = l.strip()
        if not l:
            continue
        if l.startswith('#'):
            continue
        k,v = l.split('=')
        k = k.strip()
        v = v.strip()
        config[k] = v

DEVID=config['device_id']
WIFI_SSID=config['wifi_ssid']
WIFI_PASS=config['wifi_pass']
SERVER=config['submit_endpoint']
SENSOR_HIGHEST=int(config['sensor_highest'])
SENSOR_LOWEST=int(config['sensor_lowest'])
INTERVAL_SEC=int(config['interval_sec'])

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(WIFI_SSID, WIFI_PASS)

# Define I2C pins and display resolution
i2c = machine.I2C(scl=machine.Pin(6), sda=machine.Pin(7))
display = ssd1306.SSD1306_I2C(128, 64, i2c)
adc = machine.ADC(machine.Pin(15, machine.Pin.IN))
adc.atten(machine.ADC.ATTN_11DB)
display.rotate(True)


while True:
    message = None
    ip_address = wifi.ifconfig()[0]  
    # read data
    reading = adc.read()
    reading_range = (SENSOR_HIGHEST - SENSOR_LOWEST)
    normalized_reading = (reading - SENSOR_LOWEST)
    if normalized_reading < 0:
        normalized_reading = 0
    normalized_reading = int((normalized_reading / reading_range) * 100)

    if wifi.isconnected(): 
        try:
            resp = urequests.post(SERVER, json={
                'dev_id': DEVID,
                'ip': ip_address,
                'sensor_reading': reading,
                'normalized_reading': normalized_reading
            }, timeout=5)
            if int(resp.status_code / 100) != 2:
                message = "E: HTTP " + str(resp.status_code)
            resp.close()
            message = "M: Send OK"
        except OSError as e:
            if e.value in errno.errorcode:
                message = "E: " + errno.errorcode[e.value]
            else:
                message = 'E: OSError ' + str(e.value)
    else:
        message = "E: No WiFi"

    # Clear the display
    display.fill(0)
    display.show()
    # Display text
    text = ["D: " + str(DEVID), 
            "W: " + WIFI_SSID,
            "I: " + ip_address,
            "S: " + SERVER.replace('://', '/').split('/')[1],
            "V: " + str(reading) + " " + 
            "Vn: " + str(normalized_reading)]

    if message:
        text.append(message)

    loffset = 0
    for t in text:
        display.text(t, 0, loffset, 1)
        loffset += 10
    display.show()
    time.sleep(INTERVAL_SEC)
    

    
    
