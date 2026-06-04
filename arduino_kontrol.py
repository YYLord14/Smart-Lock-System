import serial
import time
from serial.tools import list_ports

esp32 = None
BAUDRATE = 115200


def port_bul():
    portlar = list_ports.comports()

    for port in portlar:
        bilgi = f"{port.device} {port.description}".lower()

        if (
            "esp32" in bilgi
            or "ch340" in bilgi
            or "cp210" in bilgi
            or "cp210x" in bilgi
            or "usb serial" in bilgi
            or "silicon labs" in bilgi
            or "wch" in bilgi
        ):
            return port.device

    return None


def esp32_baglan():
    global esp32

    port = port_bul()

    if not port:
        print("ESP32 portu bulunamadı.")
        esp32 = None
        return

    try:
        esp32 = serial.Serial(
            port=port,
            baudrate=BAUDRATE,
            timeout=1
        )

        time.sleep(2)
        print(f"ESP32 bağlantısı başarılı: {port}")

    except Exception as e:
        esp32 = None
        print("ESP32 bağlanamadı:", e)


def veri_oku():
    if esp32 and esp32.in_waiting:
        try:
            veri = esp32.readline().decode("utf-8", errors="ignore").strip()

            if veri:
                print("ESP32 gelen veri:", veri)

            return veri

        except Exception as e:
            print("Veri okuma hatası:", e)
            return None

    return None


def komut_gonder(komut):
    if esp32:
        try:
            esp32.write((komut + "\n").encode("utf-8"))
            print("ESP32'ye gönderildi:", komut)
            return True

        except Exception as e:
            print("Komut gönderme hatası:", e)
            return False

    print("ESP32 bağlı değil, komut gönderilemedi:", komut)
    return False


def kapi_ac():
    return komut_gonder("KAPI_AC")


def esp32_kapat():
    if esp32:
        esp32.close()
        print("ESP32 bağlantısı kapatıldı.")


esp32_baglan()