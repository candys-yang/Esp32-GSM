from machine import Pin
"""Module pour connecter la carte ESP32 a un point d'acces wifi (ssid + password) et piloter un pin au choix lie a une diode led par exemple. """




def connecter(a,b):
    """ Permet de connecter la carte ESP32 au point d'acces wifi avec ssid=a password=b. Les valeurs de a et b voivent etre entre deux '...' cotes."""
    import network
    ssid = str(a)
    password = str(b)
    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.connect(ssid, password)
    while station.isconnected() == False:
        pass
    print('Connection parfaite.')
if __name__=='__main__':
    connecter('NEHDI','98582989')

def piloter(p , url):
    """ Permet de piloter un objet connecte au pin p de la carte ESP32 suite au changement d'un champ de l'adresse url."""
    from urequests import get
    from time import sleep
    led = Pin(p, Pin.OUT)
    while True:
        sleep(1)
        r = get(url)
        data=r.json()
        print("data = ",data)
        val=int(data['feeds'][1]['field1'])
        led.value(val)
if __name__=='__main__':
    url="http://api.thingspeak.com/channels/112027/feeds.json?api_key=MKL8E3Z1SZTCIUH&results=2"
    piloter(4,url)


