
import time
import os
from machine import Pin, PWM
from machine import Timer
from machine import UART



class API: 
    ''' api操作类 '''
    pass

class Net:
    ''' ESP-32 网络管理类 '''
    


class GPIO:
    ''' 管理 ESP-32 的 GPIO '''
    class Light: 
        ''' 
        初始化灯泡引脚 
        
        默认使用：
            18  红色
            19  绿色
            21  蓝色
        
        '''
        def __init__(self, red_pin=18, green_pin=19, blue_pin=22) -> None:
            self.PWM_R = PWM(Pin(red_pin))
            self.PWM_G = PWM(Pin(green_pin))
            self.PWM_B = PWM(Pin(blue_pin))

    class UART2: 
        ''' 与短信模块通讯 '''
        def __init__(self) -> None:
            ''' 初始化短信模块通讯 '''
            self.uart = UART(2, baudrate=115200)
            #初始化队列文件
            with open('read_queue.tmp','w') as f: pass
            with open('write_queue.tmp','w') as f: pass
            pass

        def Read(self): 
            ''' 从模块读取数据，并将数据写入队列 '''
            data = str(self.uart.readline())
            redata = ''
            if data not in ['None', "b'\\r\\n'"]:
                redata = data
                redata = redata.replace("b'","")
                redata = redata.replace("\\r\\n'","")
                print(redata)

            # try:
            #     data = self.uart.readline()
            #     if data is not None: 
            #         with open('read_queue.tmp','a') as f: 
            #             f.write(data)
            #     return True
            # except Exception as e: 
            #     print('Read UART Failed.', str(e))
            #     return False

        def Write(self, data:str):
            ''' 向写队列插入数据 '''
            print("Sent Command: " + data)
            self.uart.write(data + '\r\n') 

        def TcpSenData(self, serip='47.107.84.105', port='80', data='TEST'): 
            ''' 与服务器建立 tcp 并发送数据 '''

            def __write(cmd): 
                self.uart.write(cmd + '\r\n')

            _data = "$ver=1"
            
            __write('AT+CREG=1')
            __write('AT+CGDCONT=1,"IP","CMNET"')
            __write('AT+CSOCKSETPN=1')
            __write('AT+CIPMODE=0')
            __write('AT+NETOPEN')
            time.sleep(1)
            __write('AT+CIPOPEN=0,"TCP","{0}",{1}'.format(serip, port))
            time.sleep(1)
            __write('AT+CIPSEND=0,' + str(len(_data)))
            time.sleep(1)
            __write(_data)
            __write('AT+CIPCLOSE=0')
            __write('AT+NETCLOSE')

            


        


class Main:
    ''' 应用程序主类，boot.py 初始化完成后，将从这里开始应用程序 '''
    def __init__(self) -> None:
        ''' 初始化应用程序 '''
        print('Application Start.')
        
        self.uart2 = GPIO.UART2()
        # Esp32 定时器，读数据
        tim0 = Timer(0)
        tim0.init(
            period=10, mode=Timer.PERIODIC, callback=lambda t:self.uart2.Read())
        # 主循环
        while True: 
            cmd = input()
            if len(cmd) >= 1: 
                try:
                    if cmd == 'test': 
                        self.uart2.TcpSenData(data="this is test.")
                    elif cmd == 'reboot': 
                        Pin(4, Pin.OUT).value(1)
                    else:
                        self.uart2.Write(cmd)
                except Exception as e: 
                    print(str(e))



        # import uasyncio
        # async def blink(led):
        #     while True:
        #         led.on()
        #         await uasyncio.sleep_ms(100)
        #         led.off()
        #         await uasyncio.sleep_ms(100)

        # async def main(led1, led2):
        #     uasyncio.create_task(blink(led1))
        #     uasyncio.create_task(blink(led2))
        #     await uasyncio.sleep_ms(10_000)


        # # Running on a generic board
        # from machine import Pin
        # uasyncio.run(
        #     main(
        #         Pin(19, Pin.OUT), 
        #         Pin(18, Pin.OUT)
        #     )
        # )

        pass