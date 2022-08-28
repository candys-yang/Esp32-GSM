# ESP-GSM
使用 ESP32，基于AT指令实现的短信猫

## Quick start

项目目录下的 esp32-v1.18.bin 为官网下载的固件版本。

### Directory

```
.
├── Readme.md               # 说明文档
├── _env                    # Python环境（开发时）
├── app.py                  # 主程序
├── boot.py                 # 启动程序
├── config.json             # 配置文件
├── esp32-v1.18.bin         # MicroPython 固件
├── server.py               # 简单的示例服务器
└── webrepl                 # 上传工具。
```

### Install Firmware
```shell

# 删除项目的 env 环境（如果是 Macos ，则忽略）
rm -rf ./_env && python3 -m venv _env

# 切换 python 环境
source _env/bin/activate 

# 安装 esptool 工具
pip3 install esptool

# 删除固件
python3 -m esptool --port serial路径  erase_flash

# 写入固件
esptool.py --chip esp32 --port serial路径 write_flash -z 0x1000 esp32-v1.18.bin
```
```python
# 使用 serial 工具连接 ESP32 
#   如果使用 Vscode ，可安装 nRF Terminal 插件进行连接（nRF Terminal: Start terminal）
#   连接完成后，进行下面操作：（下面操作在 python命令行中进行）
import network                      # 导入网络模块
wlan = network.WLAN(network.STA_IF) # 配置为STA模式
wlan.active(True)                   # 启动无线网络
wlan.scan()                         # 扫描可用
wlan.connect('Wi-Fi名','密码')       # 加入无线

# 开启 webrepl 服务
#   执行命令后，会输出 ESP32 当前模块的IP地址和服务端口号
#       WebREPL daemon started on ws://192.168.0.120:8266
#       Started webrepl in manual override mode
import webrepl
webrepl.start(password='Esp32Room')


```

### Upload Application

```shell

# 上传程序文件到 ESP32 文件系统中。实例中的 192.168.0.120 为模块所获得的IP地址
python3 webrepl/webrepl_cli.py  boot.py 192.168.0.120:/boot.py 
python3 webrepl/webrepl_cli.py  app.py 192.168.0.120:/app.py
python3 webrepl/webrepl_cli.py  config.json 192.168.0.120:/config.json

# 按下 ESP32 的 EN键 重启模块。
```



### GPIO

ESP32 与 各个模块的连接线路。
> 注意: 模块之间必须共地。

| ESP32    | Module       | 说明                 |
|----------|--------------|---------------------|
| D18      | Red Light    | 红色灯泡             |
| D19      | Green Light  | 绿色灯泡             |
| D21      | Blue Light   | 蓝色灯泡             |
| D4       | ESP32 EN     | 连接esp32自己的en引脚 |
| RX2      | 4G Mod TX    | 连接4G模块的 Tx      |
| TX2      | 4G Mod RX    | 连接4G模块的 Rx      |



### DeployServer

将 server.py 文件上传到云服务器，并安装 Python3

```
# 安装必要的包
pip3 install flask

# 启动服务
python3 server.py 
```


## Application 

应用程序说明

### Light

> 灯泡闪烁原理，一个周期内，四种灯光颜色只会点亮 4/1 的时间，也就是说，如果有多种不正常的状态，会表现为多种颜色灯光的交替闪烁。

| 表现               | 说明                            |
|-------------------|---------------------------------|
| 灯泡模块白色灯，亮   | 系统正在启动，正在连接配置的WLAN     |
| 灯泡模块紫色灯，亮   | 正在启动文件服务                  |
| 灯泡模块绿灯，闪烁   | 表示状态正常                      |
| 灯泡模块黄灯，闪烁   | 表示网络不正常，可能信号极差        |
| 灯泡模块红灯，闪烁   | 表示无信号                       |
| 灯泡模块蓝灯，闪烁   | 表示 4G 模块没有响应 AT 指令       |
| ESP32板卡的蓝色灯亮 | 表示boot.py过程完成，进入 app.py   |
| ESP32板卡的红色灯亮 | 表示电源                         |


### Process

各个部分的程序过程

#### Firmware

    Execute boot.py --> import app.py & Execute: app.Main()

#### boot.py

    1. 设置指示灯为白色，表示boot.py开始执行
    2. 初始化WLAN（ 如果config.json 配置开启，则连接到指定 SSID ）
    3. 启动文件服务，紫色灯亮（ 如果config.json 配置开启，则开启文件服务）
    4. 加载 app.py 并执行 app.Main()
    5. 设置 GPIO.Pin4 为高电平，重启系统。（如果 app.Main() 退出）

#### app.py

    1. 初始化所需的全局变量和类
    2. 初始化 硬件定时器，执行核心代码 Timers.CycleMain()
    3. 发送 序列号查询 命令到 任务队列（TASK_QUEUE）
    4. 进入 AT 命令行模式，可随意通过ESP32的 USB Serial 发送 AT 命令。

#### Timers.CycleMain()

```
CycleMain() 是 Timers 的一个方法。
硬件定时器会不断执行这个方法，从而实现一些同步或异步命令。

周期
 ├── Exec_AT()      # 如果 TASK_QUEUE 存在任务，则执行。
 ├── Check stat     # 如果上一步没有执行，且1分钟没有执行状态检查，则执行。
 └── Exec_Read()    # 如果上面没有执行，则从 4G 模块读取数据。
```





### Network

修改 config.json 的 server 配置，设置远程服务器IP和端口（公网）

程序会定时发送状态信息到远程服务器，如果收到短信时，会发送短信到远程服务器。

请求方式：GET
```
#参考：


# 模块发送状态信息到服务器
112.97.250.211 - - [28/Aug/2022 20:25:51] "GET /stat?&p=7B27535441545F4154273A202754727565272C2027535441545F4347534E273A2027383631323130303530363136393232272C2027535441545F43534341273A20272B38363133303130323030353030272C2027535441545F4350494E273A20275245414459272C2027535441545F4347524547273A202754727565272C2027535441545F435351273A20273230277D HTTP/1.1" 200 -

# 服务器解码
{'STAT_AT': 'True', 'STAT_CGSN': '861210050616922', 'STAT_CSCA': '+8613010200500', 'STAT_CPIN': 'READY', 'STAT_CGREG': 'True', 'STAT_CSQ': '21'}

-----------------------------------

# 模块发送新消息到服务器
112.97.219.166 - - [28/Aug/2022 20:45:27] "GET /gsm?&b=30105B664E60901A301160A876849A8C8BC178014E3AFF1A0034003100390036002C67096548671F003300305206949F3002&s=106946756200636&d=2022-08-28-20:45:26 HTTP/1.1" 200 -

# 服务器解码
【学习通】您的验证码为：4196,有效期30分钟。
106946756200636
2022-08-28-20:45:26


```


### 


