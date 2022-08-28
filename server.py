'''
服务器需要部署在公网

模块使用 4G 流量对外通讯

'''
from binascii import hexlify, unhexlify
from flask import Flask, request

app = Flask(__name__)
app.debug = True

@app.route("/stat", methods=["GET"])
def stat():
    print('\r\n')
    arg = request.args
    p = unhexlify(arg['p']).decode('ascii')
    print(p)
    print('\r\n')
    return "OK"

@app.route("/gsm", methods=["GET"])
def gsm():
    print('\r\n')
    arg = request.args
    b = unhexlify(arg['b']).decode('utf-16be')
    s = arg['s']
    d = arg['d']
    print(b)
    print(s)
    print(d)
    print('\r\n')
    return "OK"


app.run('0.0.0.0')