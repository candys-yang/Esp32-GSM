#
#   主程序
#   ESP-32 短信猫
#
import json
import time
import urequests 
import esp32
import network
from machine import Timer
from machine import Pin



def StartWebREPL(pwd='Esp32'): 
    ''' 开启固件更新 '''
    import webrepl
    webrepl.start(password=pwd)


def StartNet(ssid, passwd):
    ''' 启动 Wlan 并连接无线 '''
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        print("")
        wlan.connect(ssid, passwd)
        await_time = 0
        while not wlan.isconnected():
            time.sleep(1)
            await_time += 1
            if await_time >= 30: 
                print("Connect WLAN Timeout, Skip.")
                break
        print(wlan.ifconfig())

def LoadConfig(): 
    ''' 加载配置文件 '''
    try: 
        with open('config.json','r') as f:
            return json.load(f)
    except Exception as e: 
        print("Read Config Failed. " + str(e))
        return {}

def InitNet(): 
    ''' 初始化网络配置 '''
    conf = LoadConfig()
    try:
        if conf['wlan']['active'] == True: 
            StartNet(conf['wlan']['ssid'], conf['wlan']['pwd'])
        else:
            print('Wlan No Active.')
    except Exception as e: 
        print("Init Wlan Failed",str(e))

def InitREPL():
    ''' 初始化文件服务配置 '''
    conf = LoadConfig()
    try:
        #
        if conf['wlan']['active'] is False: 
            print('Wlan No Active. REPL Skip')
            return None
        #
        if conf['webrepl']['active'] is True: 
            StartWebREPL(conf['webrepl']['pwd'])
    except Exception as e: 
        print("Init REPL Failed",str(e))


if __name__ == '__main__': 
    Pin(18, Pin.OUT).on()
    Pin(19, Pin.OUT).on()
    Pin(21, Pin.OUT).on()
    print('Start Main Program...')
    print('Init Wlan.')
    InitNet()
    Pin(19, Pin.OUT).off()
    
    print('Init REPL.')
    InitREPL()
    print('Import App Process.')
    app_light = Pin(2, Pin.OUT)
    try:
        
        app_light.value(1)
        import app
        print('Start App Process.')
        APP = app.Main()
    except Exception as e: 
        print('Start App Failed.', str(e))
    app_light.value(0)

    print('App Process Exit.')
    print('Reboot')
    time.sleep(5)
    p4 = Pin(4, Pin.OUT)
    p4.value(1)

    pass