import serial.tools.list_ports

ports = serial.tools.list_ports.comports()

print("Bağlı cihazlar:")

if not ports:
    print("Hiç seri port bulunamadı.")
else:
    for port in ports:
        print("--------------------")
        print("Port:", port.device)
        print("Açıklama:", port.description)
        print("Üretici:", port.manufacturer)
        print("HWID:", port.hwid)

        bilgi = f"{port.device} {port.description} {port.manufacturer} {port.hwid}".lower()

        if (
            "esp32" in bilgi
            or "ch340" in bilgi
            or "cp210" in bilgi
            or "cp210x" in bilgi
            or "usb serial" in bilgi
            or "silicon labs" in bilgi
            or "wch" in bilgi
        ):
            print("Tahmin: Bu port ESP32 olabilir.")