# ESP-GSM
使用 ESP32，基于AT指令实现的短信猫

## Slow Start

项目目录下的 esp32-v1.18.bin 为官网下载的固件版本。

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

# 写入miropython固件
esptool.py --chip esp32 --port serial路径 write_flash -z 0x1000 esp32-v1.18.bin

# 使用 serial 工具连接 ESP32 
#   如果使用 Vscode ，可安装 nRF Terminal 插件进行连接
#   执行vscode命令： nRF Terminal: Start terminal
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
#
import webrepl
webrepl.start(password='Esp32Room')


```

### Upload Application

```shell

# 上传程序文件到 ESP32 文件系统中。实例中的 192.168.0.120 为模块所获得的IP地址
python3 webrepl/webrepl_cli.py  boot.py 192.168.0.120:/boot.py 
python3 webrepl/webrepl_cli.py  app.py 192.168.0.120:/app.py
python3 webrepl/webrepl_cli.py  config.json 192.168.0.120:/config.json


```

### Line Interface

> ESP32 和各个模块的连接，必须要有共地端，否则，不能正常工作。

| ESP32    | Module       | 说明                 |
|----------|--------------|---------------------|
| D18      | Red Light    | 红色灯泡             |
| D19      | Green Light  | 绿色灯泡             |
| D21      | Blue Light   | 蓝色灯泡             |
| D4       | ESP32 EN     | 连接esp32自己的en引脚 |
| RX2      | 4G Mod TX    | 连接4G模块的 Tx      |
| TX2      | 4G Mod RX    | 连接4G模块的 Rx      |


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

### Server Config

短信接收服务器配置方法

在 config.json 配置文件中，修改 server 的IP和port即可。

如果使用 Serial 连接 ESP32 ，则可通过应用函数修改。

```
# 等待ESP32模块板卡的蓝灯点亮（D2），直接输入函数即可
SetServer("服务器IP","服务器端口")
```





