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


## Maintenance

当需要修改应用程序时，可参考以下方法。


### 文件上传

```
# 通过串口执行命令，连接网络和开启服务
#   boot.py 启动过程会读取 config.json 中的网络配置
#   如果 config.json 的 wlan.active = true ，则启动时会连接配置的WLAN热点
#   WebREPL 亦是如此，webrepl.active = true ，则启动文件服务。
>>> StartNet(ssid, passwd)
>>> StartWebREPL()
```

```
# 传送程序到 esp32 （IP地址为esp32的地址）
python3 webrepl/webrepl_cli.py  app.py 192.168.104.80:/app.py
```


