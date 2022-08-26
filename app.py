
import time
import os
from machine import Pin, PWM
from machine import Timer
from machine import UART

# 应用程序全局变量
STAT_CSQ = 0
STAT_CSCA = 'ERROR'   # 号码|ERROR
STAT_CPIN = 'ERROR'   # READY|ERROR
STAT_AT =   False     # 
STAT_CGREG= False     # 

class API: ...

class Net: ...

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
        def __init__(self, red_pin=18, green_pin=19, blue_pin=21) -> None:
            self.PIN_R = Pin(red_pin, Pin.OUT) 
            self.PIN_G = Pin(green_pin, Pin.OUT) 
            self.PIN_B = Pin(blue_pin, Pin.OUT) 

            self.TS = 0 # 时间分片

            self.PIN_R.off()
            self.PIN_G.off()
            self.PIN_B.off()

        def TimeMain(self):
            ''' 定时器入口函数，做一只快乐的小灯泡 
            
                NOTE:
                    绿色    正常
                    黄色    断网
                    红色    无信号
                    蓝色    模块异常

            '''
            #
            global STAT_CSCA, STAT_CPIN, STAT_CSQ, STAT_AT
            #
            # 时间片
            self.TS += 1
            if self.TS > 100: self.TS = 0
            #
            self.PIN_R.value(0)
            self.PIN_G.value(0)
            self.PIN_B.value(0)
            # 绿灯的时间分片
            if self.TS >= 1 and self.TS <= 24: 
                isopen = True
                if STAT_CSQ <= 14: isopen = False
                if STAT_CSCA == "ERROR": isopen = False
                if STAT_CPIN == "ERROR": isopen = False
                if STAT_AT == False: isopen = False
                if STAT_CGREG == False: isopen = False
                #
                if isopen:
                    self.PIN_G.value(1)
                pass
            # 黄灯的时间分片
            if self.TS >= 25 and self.TS <= 49: 
                isopen = False
                if STAT_CGREG == False: isopen = True
                #
                if isopen:
                    self.PIN_R.value(1)
                    self.PIN_G.value(1)
                pass
            # 红灯的时间分片
            if self.TS >= 50 and self.TS <= 74: 
                isopen = False
                if STAT_CSQ <= 1: isopen = True
                if STAT_CPIN != "READY": isopen = True
                #
                if isopen:
                    self.PIN_R.value(1)
                pass
            # 蓝灯的时间分片
            if self.TS >= 75 and self.TS <= 100: 
                if STAT_AT is False:
                    self.PIN_B.value(1)
                pass
            
            pass

    class UART2: 
        ''' 与短信模块通讯 '''
        def __init__(self) -> None:
            ''' 初始化短信模块通讯 '''
            self.uart = UART(2, baudrate=115200)
            self.TIME_RW_COUNTS = 0
            self.READ_QUEUE = []
            pass

        def Read(self): 
            ''' 
            从模块读取数据，并发送到队列。 
            
            NOTE: 
                当收到响铃消息时，将自动发送挂断命令
            '''
            readrow = self.uart.readline()
            if readrow is not None: 
                data = str(readrow.decode('ascii'))
                if data in ['\r', '\n', '\r\n', '\n\r']: 
                    return None
                data = data.replace('\r','').replace('\n','')
                # 处理来电事件，发送挂断操作
                if data.find("+CGEV:") == 0: 
                    self.Write("AT+CHUP")
                    return None
                if data.find('RING') == 0: 
                    self.Write("AT+CHUP")
                    return None
                # 处理新短信事件，调用新短信方法
                if data.find('+CMTI:') == 0: 
                    self.New_MsgEvent()
                    return None
                # 一般消息处理
                self.READ_QUEUE.append(str(data))
                if data == 'OK':
                    self.Read_Sorting()
                if data == 'ERROR': 
                    self.Read_Sorting()
                if data.find("+CMS ERROR:") == 0: 
                    self.Read_Sorting()
                if data.find("+CME ERROR:") == 0: 
                    self.Read_Sorting()

        def Write(self, data:str):
            ''' 向写队列插入数据 '''
            print("Sent Command: " + data)
            self.uart.write(data + chr(13)) 

        def TcpSenData(self, serip, port, types, data): 
            ''' 
            与服务器建立 tcp 并发送数据 
            
            Args:
                serip:  服务器IP
                port:   服务端口
                types:  数据类型
                data:   数据

            Example:
                self.uart2.TcpSenData(
                    serip='47.104.187.138',
                    port='8266',
                    types='MSG',
                    data="this is test.")

            '''

            def __write(cmd): 
                self.uart.write(cmd + '\r\n')

            _data = "$DATA_MATE=V1,{0}${1}".format(types, data)
            
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

        def TimeRW(self): 
            ''' 定时器主线程，负责轮询模块读缓冲，定期写任务 '''
            self.TIME_RW_COUNTS += 1
            if self.TIME_RW_COUNTS >= 1000:   
                global STAT_AT
                STAT_AT = False
                self.Write("AT")
                self.Write("AT+CSQ")            # 信号质量
                self.Write("AT+CSCA?")          # 运营商
                self.Write("AT+COPS?")          # 短信中心
                self.Write("AT+CPIN?")          # sin卡状态
                self.Write("AT+CPMS?")          # 短信数量
                self.Write("AT+CGREG?")         # 与运营商注册状态
                #
                self.TIME_RW_COUNTS = 0
            self.Read()

        def Read_Sorting(self):
            ''' 
            Read方法读取到 OK 后，调用此函数对命令进行分拣处理 
            
            NOTE: 
                这里不会处理新短信的消息，因为事件消息没有 OK 回显
            '''
            read_data = self.READ_QUEUE
            # 解析数据
            if read_data[0] == "AT": 
                global STAT_AT
                STAT_AT = True
            if read_data[0] == "AT+CSQ":
                csq_mate = str(read_data[1])
                csq_v = csq_mate.replace("+CSQ: ","").rsplit(',')
                global STAT_CSQ
                STAT_CSQ = int(csq_v[0])
            if read_data[0] == "AT+CSCA?": 
                mate = str(read_data[1])
                global STAT_CSCA
                if mate.find("ERROR") >= 0: 
                    STAT_CSCA = "ERROR"
                else:
                    v = mate.replace("+CSCA: ","").rsplit(',')
                    v = v[0].replace("\"","")
                    STAT_CSCA = v
            if read_data[0] == "AT+CPIN?": 
                mate = str(read_data[1])
                global STAT_CPIN
                if mate.find("READY") >= 0: 
                    STAT_CPIN = 'READY'
                else:
                    STAT_CPIN = 'ERROR'
            if read_data[0] == "AT+CGREG?": 
                mate = str(read_data[1])
                global STAT_CGREG
                if mate.find("+CGREG: 0,1") >= 0: 
                    STAT_CGREG = True
                else:
                    STAT_CGREG = False

            print("Receive ---> ",read_data)
            self.READ_QUEUE.clear()
            pass

        def New_MsgEvent(self): 
            ''' 收到新消息的事件 '''
            print("New Messages.")
             
            pass

class Main:
    ''' 应用程序主类，boot.py 初始化完成后，将从这里开始应用程序 '''
    def __init__(self) -> None:
        ''' 初始化应用程序 '''
        print('Application Start.')
        
        self.uart2 = GPIO.UART2()
        self.light = GPIO.Light()
        # Esp32 定时器，读数据
        self.tim0 = Timer(0)
        self.tim0.init(
            period=50, mode=Timer.PERIODIC, callback=lambda t:self.uart2.TimeRW())
        # Esp32 定时器，指示灯
        self.tim1 = Timer(1)
        self.tim1.init(
            period=50, mode=Timer.PERIODIC, callback=lambda t:self.light.TimeMain())
        
        # 初始化短信模块必要的参数   
        self.uart2.Write('AT+CMGF=1')
        self.uart2.Write('AT+CSCS="GSM"')
        self.uart2.Write('AT+CNMI=2,1')

        # 主循环
        while True: 
            cmd = input()
            if len(cmd) >= 1: 
                try:
                    if cmd == 'STAT': 
                        global STAT_CSQ
                        global STAT_CSCA
                        global STAT_CPIN
                        global STAT_AT
                        global STAT_CGREG
                        print("STAT_CSQ=" + str(STAT_CSQ))
                        print("STAT_CSCA=" + str(STAT_CSCA))
                        print("STAT_CPIN=" + str(STAT_CPIN))
                        print("STAT_AT=" + str(STAT_AT))
                        print("STAT_CGREG=" + str(STAT_CGREG))
                        pass
                    elif cmd == 'reboot': 
                        Pin(4, Pin.OUT).value(1)
                    else:
                        self.uart2.Write(cmd)
                except Exception as e: 
                    print(str(e))


        pass