import cv2
import sqlite3
import datetime
import subprocess
import sys
import time
import os
from playsound import playsound
from arduino_kontrol import veri_oku, kapi_ac, komut_gonder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_NAME = os.path.join(BASE_DIR, "fabrika.db")
TRAINER_FILE = os.path.join(BASE_DIR, "trainer.yml")

SUCCESS_SOUND = os.path.join(BASE_DIR, "ses1_1.wav")
FAIL_SOUND = os.path.join(BASE_DIR, "ses2_2.wav")

CONFIDENCE_LIMIT = 60
FACE_SCAN_DURATION = 10
CARD_COOLDOWN = 3

panel_process = None

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def ses_cal(dosya):
    if os.path.exists(dosya):
        playsound(dosya)
    else:
        print(f"Ses dosyası bulunamadı: {dosya}")


def recognizer_yukle():
    if not os.path.exists(TRAINER_FILE):
        print("trainer.yml bulunamadı. Önce şef panelinden yüz kaydı yapmalısınız.")
        return None

    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read(TRAINER_FILE)
        return recognizer
    except Exception as e:
        print("Yüz tanıma modeli yüklenemedi:", e)
        return None


def personel_getir(pid):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT ad, soyad, statu FROM personel WHERE id=?", (pid,))
    data = cursor.fetchone()
    conn.close()
    return data


def son_islem_getir(pid):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT islem
        FROM giris_logs
        WHERE personel_id=?
        ORDER BY giris_zamani DESC
        LIMIT 1
    """, (pid,))
    data = cursor.fetchone()
    conn.close()

    if data:
        return data[0]

    return None


def yeni_islem_belirle(pid):
    son_islem = son_islem_getir(pid)

    if son_islem == "GIRIS":
        return "CIKIS"

    return "GIRIS"


def log_ekle(pid, ad, soyad, statu, islem):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO giris_logs (personel_id, ad, soyad, statu, islem, giris_zamani)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        pid,
        ad,
        soyad,
        statu,
        islem,
        datetime.datetime.now()
    ))
    conn.commit()
    conn.close()


def panel_ac():
    global panel_process

    if panel_process is not None and panel_process.poll() is None:
        print("Panel zaten açık.")
        return

    panel_yolu = os.path.join(BASE_DIR, "sef_panel.py")
    panel_process = subprocess.Popen([sys.executable, panel_yolu], cwd=BASE_DIR)
    print("Panel açıldı.")


def kamera_ac():
    kamera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not kamera.isOpened():
        kamera = cv2.VideoCapture(1, cv2.CAP_DSHOW)

    if not kamera.isOpened():
        print("Kamera açılamadı!")
        return None

    kamera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return kamera


def yuz_tanima_yap():
    recognizer = recognizer_yukle()

    if recognizer is None:
        komut_gonder("ONAY_RED")
        ses_cal(FAIL_SOUND)
        panel_ac()
        return False

    kamera = kamera_ac()

    if kamera is None:
        komut_gonder("ONAY_RED")
        ses_cal(FAIL_SOUND)
        panel_ac()
        return False

    print("Kart okundu, kamera açıldı")
    komut_gonder("KAMERA_ACIK")

    found = False
    finished = False
    personel = None
    yapilacak_islem = None

    start_time = time.time()

    while not finished and time.time() - start_time < FACE_SCAN_DURATION:
        ret, frame = kamera.read()

        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        status = "YUZ BEKLENIYOR..."

        for (x, y, w, h) in faces:
            face = gray[y:y+h, x:x+w]
            face = cv2.resize(face, (200, 200))

            try:
                id_, confidence = recognizer.predict(face)
            except Exception as e:
                print("Tanıma hatası:", e)
                status = "TANIMA HATASI"
                finished = True
                break

            if confidence < CONFIDENCE_LIMIT:
                data = personel_getir(id_)

                if data:
                    ad, soyad, statu = data

                    yapilacak_islem = yeni_islem_belirle(id_)
                    personel = (id_, ad, soyad, statu)
                    found = True
                    finished = True

                    if yapilacak_islem == "GIRIS":
                        status = f"{ad} {soyad} - GIRIS ONAYLANDI"
                    else:
                        status = f"{ad} {soyad} - CIKIS ONAYLANDI"

                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    break

                status = "PERSONEL KAYDI YOK"
                found = False
                finished = True
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                break

            status = "TANINMADI"
            found = False
            finished = True
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
            break

        cv2.putText(
            frame,
            status,
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0) if found else (0, 255, 255),
            2
        )

        cv2.imshow("Kilit Sistemi", frame)
        cv2.waitKey(1)

    if found and personel:
        pid, ad, soyad, statu = personel

        print("ONAYLANDI:", ad, soyad, statu, yapilacak_islem)

        log_ekle(pid, ad, soyad, statu, yapilacak_islem)

        komut_gonder("ONAY_OK")

        ses_cal(SUCCESS_SOUND)

        kapi_ac()

    else:
        print("TANINMADI")
        komut_gonder("ONAY_RED")
        ses_cal(FAIL_SOUND)

    kamera.release()
    cv2.destroyAllWindows()

    panel_ac()

    return found


print("Sistem hazır. ESP32 kart sinyali bekleniyor...")
komut_gonder("BAGLANTI_OK")

son_kart_zamani = 0

while True:
    veri = veri_oku()

    if veri == "KART_OKUNDU":
        simdi = time.time()

        if simdi - son_kart_zamani < CARD_COOLDOWN:
            print("Kart sinyali tekrar geldi, bekleme süresi nedeniyle yok sayıldı.")
            time.sleep(0.1)
            continue

        son_kart_zamani = simdi

        print("Kart sinyali alındı.")
        yuz_tanima_yap()
        print("İşlem tamamlandı. Yeni kart bekleniyor...")

    time.sleep(0.1)