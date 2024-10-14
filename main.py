import network
import socket
import time
from machine import Pin
from dht import DHT11

# DHT11 Sensörünü Tanımla
dht_sensor = DHT11(Pin(4))

# LED tanımlama (GP17 pini)
led = Pin(17, Pin.OUT)

# Wi-Fi AP Ayarları
SSID = 'PicoW_AP'
PASSWORD = '12345678'

# Access Point Oluşturma
def create_access_point():
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=SSID, password=PASSWORD)
    ap.active(True)
    while not ap.active():
        pass
    print("Access Point aktif!")
    print("IP adresi:", ap.ifconfig()[0])
    return ap.ifconfig()[0]

# DHT11 verilerini okuma ve LED kontrolü
def read_dht11():
    try:
        dht_sensor.measure()
        temp = dht_sensor.temperature()
        humidity = dht_sensor.humidity()

        # Sıcaklık 30°C'den fazla ise LED'i yak
        if temp > 30:
            led.on()
        else:
            led.off()

        return temp, humidity
    except OSError as e:
        print("DHT11 sensöründe hata:", e)
        return None, None

# HTTP Sunucusu
def serve(ip):
    addr = socket.getaddrinfo(ip, 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('Sunucu dinliyor, şu URL\'yi tarayıcıda ziyaret edin:', ip)

    while True:
        cl, addr = s.accept()
        print('Yeni bağlantı:', addr)
        request = cl.recv(1024).decode()
        print('İstek:', request)

        # DHT11 verilerini oku
        temperature, humidity = read_dht11()

        # Web sayfası içeriği (sayfa her 5 saniyede bir yenilenir)
        html = f"""
        <html>
        <head>
            <title>Pico W Sıcaklık ve Nem</title>
            <meta charset="UTF-8">
            <meta http-equiv="refresh" content="5"> <!-- Sayfa her 5 saniyede bir yenilenir -->
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    text-align: center;
                    background-color: #f4f4f4;
                    padding: 50px;
                }}
                h1 {{
                    color: #333;
                }}
                .data-box {{
                    background-color: #fff;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
                    display: inline-block;
                    margin-top: 30px;
                }}
                .data-box h2 {{
                    font-size: 2.5em;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <h1>Raspberry Pi Pico W ile Sıcaklık ve Nem Takibi</h1>
            <div class="data-box">
                <h2>Sıcaklık: {temperature}°C</h2>
                <h2>Nem: {humidity}%</h2>
                <h2>LED Durumu: {"Yanıyor" if temperature > 30 else "Sönük"}</h2>
            </div>
        </body>
        </html>
        """

        # HTTP yanıtı gönder
        cl.send('HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=UTF-8\r\n\r\n')
        cl.send(html)
        cl.close()

# Access Point'i başlat ve sunucuyu çalıştır
ip = create_access_point()
serve(ip)
