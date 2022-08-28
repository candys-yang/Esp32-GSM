'''
Esp32 GSM 的主要逻辑代码

NOTE: 
    短信模块的交互：
        轮询事件:   
            使用 ESP32 硬件定时器（time0），循环调用 TimeRW()
        接收数据:   
            TimeRW()函数会调用 UART.readline() 
            数据不为 None 、\\r\\n ，则判定为有效的接收数据。
            收到有效数据，将调用 Read_Sorting() 方法进行数据处理。
        数据格式：
            [原始命令, 响应数据, 响应数据（如果有多个响应数据）, 'OK']
        发送命令:   
            发送命令直接调用 GPIO.UART2.Write() 不推荐在开发中直接调用 uart.write()
    
    短信读取流程:
        TimeRW()

'''
import time
import os
from binascii import unhexlify, hexlify
from machine import Pin, PWM
from machine import Timer
from machine import UART


# 应用程序全局变量
STAT_CSQ = 0
STAT_CSCA = 'ERROR'   # 号码|ERROR
STAT_CPIN = 'ERROR'   # READY|ERROR
STAT_AT =   False     # 
STAT_AT_TIME = 0      #
STAT_CGREG= False     # 
STAT_CHECK_TIME = 0   # 下次状态检查时间

TASK_QUEUE = []
READ_QUEUE = []       #完整的命令结果，如：  [ ['AT+CSQ','xxxxxxxxx','OK'], ... ]

class API: ...

class Net: 
    ''' 网络传输 '''
    def __init__(self, uart) -> None: self.uart = uart

    def SentSTAT(self): 
        ''' 发送状态数据到远程服务器 '''
        global STAT_CSQ, STAT_CSCA, STAT_CPIN, STAT_AT, STAT_CGREG
        self.uart.Write('AT+HTTPINIT')
        data = {
            "STAT_CSQ": STAT_CSQ, 
            "STAT_CSCA": STAT_CSCA, 
            "STAT_CPIN": STAT_CPIN, 
            "STAT_AT": STAT_AT, 
            "STAT_CGREG": STAT_CGREG}
        data = hexlify(str(data).encode('utf-16be')).decode('ascii').upper()
        self.uart.Write(
            'AT+HTTPPARA="URL","http://47.104.187.138:5000/stat?&p={0}"'.format(
                data
            ))
        self.uart.Write('AT+HTTPACTION=0')
        # 读取返回
        self.uart.Write('AT+HTTPHEAD')
        # 关闭http对象
        self.uart.Write('AT+HTTPTERM')

        pass

    def SentGSM(self, gsm_body, gsm_source, gsm_date): 
        ''' 发送短信到远程服务器 '''
        self.uart.Write('AT+HTTPINIT')
        self.uart.Write(
            'AT+HTTPPARA="URL","http://47.104.187.138:5000/gsm?&b={0}&s={1}&d={2}"'\
            .format(gsm_body, gsm_source, gsm_date))
        self.uart.Write('AT+HTTPACTION=0')
        # 读取返回
        self.uart.Write('AT+HTTPHEAD')
        # 关闭http对象
        self.uart.Write('AT+HTTPTERM')
        pass


class MSG: 
    ''' 
    对短信进行解析处理 
    '''
    def __init__(self, uart) -> None: self.uart = uart

    def ReadMate(self, data): 
        ''' 读取模块原始的短信数据 '''
        print('ReadMate ---> ', data)
        s = 0
        head = ''
        body = ''
        for i in data: 
            if str(i) == 'OK': break
            if s == 1: head = str(i)
            if s >= 2: body += str(i)
            s += 1
        #
        print("ReadMate.head ---> ", head)
        print("ReadMate.body ---> ", body)
        # 处理头信息
        head_list = head.replace("\"","").rsplit(',')
        source = head_list[1]
        d_list = str(head_list[3]).rsplit("/")
        t_list = str(head_list[4]).rsplit(":")
        dates = "{0}-{1}-{2} {3}:{4}:{5}".format(
            "20" + str(d_list[0]),
            str(d_list[1]),
            str(d_list[2]),
            str(t_list[0]),
            str(t_list[1]),
            str(t_list[2]).replace("+32",""),
            )
        print('ReadMate.head.source ---> ', source)
        print('ReadMate.head.dates  ---> ', dates)
        net = Net(self.uart)
        net.SentGSM(body, source, dates)
    pass

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
                else:
                    if self.TS <= 40: self.TS += 5
                pass
            # 红灯的时间分片
            if self.TS >= 50 and self.TS <= 74: 
                isopen = False
                if STAT_CSQ <= 1: isopen = True
                if STAT_CPIN != "READY": isopen = True
                #
                if isopen:
                    self.PIN_R.value(1)
                else:
                    if self.TS <= 70: self.TS += 5
                pass
            # 蓝灯的时间分片
            if self.TS >= 75 and self.TS <= 100: 
                if STAT_AT is False:
                    self.PIN_B.value(1)
                else:
                    if self.TS <= 90: self.TS += 5
            
            pass

    class Uart:
        ''' 短信模块通讯类 '''
        def __init__(self) -> None:
            ''' 初始化短信模块通讯类 '''
            self.uart = UART(2, baudrate=115200)

        def ReadOne(self): 
            ''' 
            读取一个完整的返回信息（此方法不会将返回值写入 READ_QUEUE）
            
            Return: [原始命令,返回数据,...,结束字符]
            '''
            redata = []
            _exec_time = time.time()
            while True:
                # 超时处理
                if _exec_time <= time.time() - 5: 
                    print('Read AT Timeout, Try redata=' + str(redata))                    
                    return None
                #
                readrow = self.uart.readline()
                if readrow is not None: 
                    data = str(readrow.decode('ascii'))
                    data = data.replace('\r','').replace('\n','')
                    # 如果是空行，退出本次循环
                    if data not in ['\r', '\n', '\r\n', '\n\r', '']: 
                        print('DEBUG.URAT.RecData: ', data, '<--|')
                        # 来电消息、新短信，立即返回
                        if data.find("+CGEV:") == 0: return ['+CGEV', data, 'OK']
                        if data.find('+CLCC:') == 0: return ['+CLCC', data, 'OK']
                        if data.find('RING') == 0:  return ['RING', data, 'OK']
                        if data.find('VOICE CALL') == 0: return ['VOICE CALL', data, 'OK']
                        if data.find('+CMTI') == 0: return ['+CMTI', data, 'OK']
                        # 其它消息，立即返回
                        if data.find('*ATREADY') == 0: return ['*ATREADY', data, 'OK']
                        #if data.find('+CPIN') == 0: return ['+CPIN', data, 'OK']
                        if data.find('SMS DONE') == 0: return ['SMS DONE', data, 'OK']
                        if data.find('PB DONE') == 0: return ['PB DONE', data, 'OK']

                        # 记录分片输出
                        redata.append(str(data))
                        # 命令完结，退出
                        if data in ['OK','ERROR']:  return redata
                        if data.find("+CMS ERROR:") == 0: return redata
                        if data.find("+CME ERROR:") == 0: return redata

        def ReadAll(self):
            ''' 一次性读取所有数据并存放到 READ_QUEUE 队列中 '''
            while True: 
                data = self.ReadOne()
                if data is not None: READ_QUEUE.append(data)
                if data is None: return None
                 
        def Write(self, data, chr13=True): 
            ''' 向模块发送AT命令 '''
            print("SentAT: ", data)
            if chr13: self.uart.write(data + chr(13)) 
            else: self.uart.write(data)

class Timers: 
    ''' 
    硬件定时器 

    NOTE:
    
    '''
    def __init__(self, uart:GPIO.Uart) -> None:
        ''' 初始化定时器操作对象 '''
        self.uart = uart
        self.light = GPIO.Light()
        self.time_count = 6000
        self.time_count_unixt = time.time()
        pass

    def CycleMain(self):
        ''' 
        周期入口 
        
        如果当前有 TASK_QUEUE ，则不会执行 Exec_Read()

        这些方法在一个 CycleMain 周期里是互斥的:
            Exec_Read()  
            Exec_AT()
        '''
        # 周期所需时间统计
        if self.time_count <= 0:
            self.time_count = 6000
            ct = time.time()
            print('Timer 0 , 6000 cycles RunTime:', ct - self.time_count_unixt )
            self.time_count_unixt = ct
        else:
            self.time_count -= 1
        #
        if self.time_count % 5 == 0: self.light.TimeMain()
        #
        global TASK_QUEUE, STAT_CHECK_TIME
        # 互斥任务
        if len(TASK_QUEUE) >= 1:
            print("DEBUG.CYCLE:TASK_QUEUE")
            q = TASK_QUEUE.pop()
            if q['type'] == 'at': self.Exec_AT(q)
            print("DEBUG.CYCLE:TASK_QUEUE----------END")
        elif STAT_CHECK_TIME <= time.time():  # 判断是否应该检查状态
            print("DEBUG.CYCLE:STAT_CHECK_TIME")
            # 每隔60秒后，检查一次状态
            STAT_CHECK_TIME = time.time() + 60 
            self.Exec_AT({"type": "at", "data": "AT", "callback": READ_QUEUE.append})
            self.Exec_AT({"type": "at", "data": "AT+CSQ", "callback": READ_QUEUE.append})
            self.Exec_AT({"type": "at", "data": "AT+CSCA?", "callback": READ_QUEUE.append})
            self.Exec_AT({"type": "at", "data": "AT+COPS?", "callback": READ_QUEUE.append})
            self.Exec_AT({"type": "at", "data": "AT+CPIN?", "callback": READ_QUEUE.append})
            self.Exec_AT({"type": "at", "data": "AT+CPMS?", "callback": READ_QUEUE.append})
            self.Exec_AT({"type": "at", "data": "AT+CGREG?", "callback": READ_QUEUE.append})
            print("DEBUG.CYCLE:STAT_CHECK_TIME----------END")
            net = Net(self.uart)
            net.SentSTAT()
        else:
            self.Exec_Read()

    def Exec_Read(self): 
        ''' 定时读取 '''
        global READ_QUEUE
        global STAT_CSQ, STAT_CSCA, STAT_CPIN, STAT_AT, STAT_CGREG, STAT_AT_TIME
        # 判断模块是否有需要读取的信息
        if self.uart.uart.any() >= 1: 
            data = self.uart.ReadOne() 
            READ_QUEUE.append(data)
        # 读取 READ_QUEUE 队列并处理
        if len(READ_QUEUE) >= 1:
            qd = READ_QUEUE.pop()
            print("READ_QUEUE POP: ", qd)
            # 来电，直接挂断
            if qd[0] == 'RING':
                self.Exec_AT({'type':'at','data':'AT+CHUP','callback': print})
            # 新短信处理
            if qd[0].find('+CMTI') == 0: 
                msgindex = data[1].rsplit(",")
                self.Exec_AT({'type':'at','data':'AT+CMGF=1','callback': print})
                self.Exec_AT({'type':'at','data':'AT+CSCS="GSM"','callback': print})
                self.Exec_AT(
                    {'type':'at','data':'AT+CMGR=' + msgindex[1],'callback': MSG(self.uart).ReadMate})
            # 处理状态信息
            #   信号
            if qd[0] == 'AT+CSQ': 
                try:
                    STAT_CSQ = int(str(qd[1]).replace("+CSQ: ","").rsplit(',')[0])
                except:
                    STAT_CSQ = 0
            #   命令响应
            if qd[0] == 'AT': 
                STAT_AT_TIME = time.time()
                STAT_AT = True
            #   sin卡连接
            if qd[0] == 'AT+CPIN?': 
                if str(qd[1]).find('READY') >= 0: 
                    STAT_CPIN = 'READY'
                else:
                    STAT_CPIN = 'ERROR'
            #   注册状态
            if qd[0] == 'AT+CGREG?': 
                if str(qd[1]).find('0,1') >= 0: 
                    STAT_CGREG = True
                else:
                    STAT_CGREG = False
            #   中心号码
            if qd[0] == 'AT+CSCA?': 
                mate = str(qd[1])
                if mate.find("ERROR") >= 0: 
                    STAT_CSCA = "ERROR"
                else:
                    v = mate.replace("+CSCA: ","").rsplit(',')
                    v = v[0].replace("\"","")
                    STAT_CSCA = v
            #
        # STAT_AT_TIME 过期状态更新
        if STAT_AT_TIME + 60 <= time.time(): 
            STAT_AT = False

        pass

    def Exec_AT(self, taskdata):
        ''' 
        执行AT任务
        执行结果不会发送到 READ_QUEUE。除非 callback 为 READ_QUEUE.append

        Args:
            taskdata: 
                {"type": "at", "data": AT命令内容, "callback": 回调函数 }
        
        '''
        print("DEBUG:UART:Exec_AT: ", taskdata['data'])
        if self.uart.uart.any() >= 1: self.uart.ReadAll()
        self.uart.Write(taskdata['data'])
        redata = self.uart.ReadOne()
        try:
            fun = taskdata['callback']
            fun(redata)
        except Exception as e:
            print("Exec AT CallBack Try:", str(e))


class Cmd: 
    ''' 内置命令 '''
    def __init__(self) -> None: ...

    def Stat(self):
        ''' 显示当前状态 '''
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



class Main:
    ''' 应用程序主类，boot.py 初始化完成后，将从这里开始应用程序 '''
    def __init__(self) -> None:
        ''' 初始化应用程序 '''
        print('Application Start.')
        #
        global TASK_QUEUE
        #
        cmd = Cmd()
        uart = GPIO.Uart()
        timers = Timers(uart)
        # Esp32 定时器，读数据
        self.tim0 = Timer(0)
        self.tim0.init(
            period=10, mode=Timer.PERIODIC, 
            callback=lambda p:timers.CycleMain())


        # 主循环
        while True: 
            __c = input()
            if len(__c) >= 1: 
                try:
                    if __c == 'STAT': cmd.Stat()
                    elif __c == 'reboot': Pin(4, Pin.OUT).value(1)
                    else: 
                        TASK_QUEUE.append({
                            "type": "at", 
                            "data": __c,
                            "callback": print
                        })
                except Exception as e: 
                    print(str(e))