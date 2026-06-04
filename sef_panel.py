import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import time
import cv2
import numpy as np
from veritabani import veritabani_baslat

veritabani_baslat()

DB_NAME = "fabrika.db"

DATASET_DIR = "dataset"
TRAINER_FILE = "trainer.yml"
SAMPLE_COUNT = 30

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def baglan():
    return sqlite3.connect(DB_NAME)


def yuz_kaydi_yap(pid, ad, soyad):
    os.makedirs(DATASET_DIR, exist_ok=True)

    kamera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not kamera.isOpened():
        kamera = cv2.VideoCapture(1, cv2.CAP_DSHOW)

    if not kamera.isOpened():
        messagebox.showerror("Kamera Hatası", "Kamera açılamadı!")
        return 0

    kamera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    kayit_sayisi = 0
    start_time = time.time()
    max_duration = 25
    last_capture_time = 0

    while kayit_sayisi < SAMPLE_COUNT and time.time() - start_time < max_duration:
        ret, frame = kamera.read()

        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        status = f"{ad} {soyad} - Yuz kaydi: {kayit_sayisi}/{SAMPLE_COUNT}"

        for (x, y, w, h) in faces:
            face = gray[y:y+h, x:x+w]
            face = cv2.resize(face, (200, 200))

            if time.time() - last_capture_time > 0.15:
                kayit_sayisi += 1
                last_capture_time = time.time()

                dosya_yolu = os.path.join(
                    DATASET_DIR,
                    f"person.{pid}.{kayit_sayisi}.jpg"
                )

                cv2.imwrite(dosya_yolu, face)

            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            break

        cv2.putText(
            frame,
            status,
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )

        cv2.imshow("Yuz Kaydi", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    kamera.release()
    cv2.destroyAllWindows()

    return kayit_sayisi


def modeli_yenile():
    faces = []
    ids = []

    if not os.path.exists(DATASET_DIR):
        if os.path.exists(TRAINER_FILE):
            os.remove(TRAINER_FILE)
        return False

    for dosya in os.listdir(DATASET_DIR):
        if not dosya.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        parcalar = dosya.split(".")

        if len(parcalar) < 4:
            continue

        try:
            pid = int(parcalar[1])
        except ValueError:
            continue

        dosya_yolu = os.path.join(DATASET_DIR, dosya)
        image = cv2.imread(dosya_yolu, cv2.IMREAD_GRAYSCALE)

        if image is None:
            continue

        image = cv2.resize(image, (200, 200))

        faces.append(image)
        ids.append(pid)

    if not faces:
        if os.path.exists(TRAINER_FILE):
            os.remove(TRAINER_FILE)
        return False

    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
    except AttributeError:
        messagebox.showerror(
            "OpenCV Hatası",
            "cv2.face bulunamadı. opencv-contrib-python kurulu olmalı."
        )
        return False

    recognizer.train(faces, np.array(ids, dtype=np.int32))
    recognizer.write(TRAINER_FILE)

    return True


def personel_ekle():
    ad = entry_ad.get().strip()
    soyad = entry_soyad.get().strip()
    statu = entry_statu.get().strip()

    if not ad or not soyad or not statu:
        messagebox.showwarning(
            "Eksik Bilgi",
            "Lütfen ad, soyad ve statü alanlarını doldurun."
        )
        return

    conn = baglan()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO personel (ad, soyad, statu)
        VALUES (?, ?, ?)
    """, (ad, soyad, statu))

    pid = cursor.lastrowid

    conn.commit()
    conn.close()

    personel_tablo_guncelle()

    messagebox.showinfo(
        "Yüz Kaydı",
        "Personel eklendi. Şimdi kamera açılacak. Yüzünüzü kameraya gösterin."
    )

    kayit_sayisi = yuz_kaydi_yap(pid, ad, soyad)

    if kayit_sayisi > 0:
        if modeli_yenile():
            messagebox.showinfo(
                "Başarılı",
                f"Personel ve yüz kaydı tamamlandı. Alınan yüz kaydı: {kayit_sayisi}"
            )
        else:
            messagebox.showwarning(
                "Model Hatası",
                "Yüz kaydı alındı ama trainer.yml güncellenemedi."
            )
    else:
        messagebox.showwarning(
            "Yüz Kaydı Yok",
            "Personel eklendi ama yüz kaydı alınamadı."
        )

    entry_ad.delete(0, tk.END)
    entry_soyad.delete(0, tk.END)
    entry_statu.delete(0, tk.END)

    personel_tablo_guncelle()


def personel_sil():
    secili = personel_tree.selection()

    if not secili:
        messagebox.showwarning(
            "Seçim Yok",
            "Lütfen silmek istediğiniz personeli tablodan seçin."
        )
        return

    item = personel_tree.item(secili[0])
    values = item["values"]

    pid = values[0]
    ad = values[1]
    soyad = values[2]

    cevap = messagebox.askyesno(
        "Personel Sil",
        f"{ad} {soyad} adlı personeli silmek istiyor musunuz?"
    )

    if not cevap:
        return

    conn = baglan()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM personel WHERE id=?", (pid,))

    conn.commit()
    conn.close()

    if os.path.exists(DATASET_DIR):
        for dosya in os.listdir(DATASET_DIR):
            if dosya.startswith(f"person.{pid}."):
                os.remove(os.path.join(DATASET_DIR, dosya))

    modeli_yenile()
    personel_tablo_guncelle()

    messagebox.showinfo(
        "Silindi",
        "Personel ve bu personele ait yüz kayıtları silindi."
    )


def personel_getir():
    conn = baglan()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, ad, soyad, statu
        FROM personel
        ORDER BY id DESC
    """)

    data = cursor.fetchall()
    conn.close()
    return data


def personel_tablo_guncelle():
    for item in personel_tree.get_children():
        personel_tree.delete(item)

    for row in personel_getir():
        personel_tree.insert("", "end", values=row)


def log_getir():
    conn = baglan()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, personel_id, ad, soyad, statu, islem, giris_zamani
        FROM giris_logs
        ORDER BY id DESC
    """)

    data = cursor.fetchall()
    conn.close()
    return data


def log_tablo_guncelle():
    for item in log_tree.get_children():
        log_tree.delete(item)

    for row in log_getir():
        log_tree.insert("", "end", values=row)

    root.after(1000, log_tablo_guncelle)


root = tk.Tk()
root.title("ŞEF PANELİ - PERSONEL VE GİRİŞ ÇIKIŞ")
root.geometry("1120x650")


baslik = tk.Label(
    root,
    text="ŞEF PANELİ",
    font=("Arial", 18, "bold")
)
baslik.pack(pady=10)


notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=10, pady=10)


# =========================
# PERSONEL KAYIT SEKİMESİ
# =========================
personel_frame = ttk.Frame(notebook)
notebook.add(personel_frame, text="Personel Kayıtları")


form_frame = ttk.LabelFrame(personel_frame, text="Yeni Personel Ekle")
form_frame.pack(fill="x", padx=10, pady=10)


tk.Label(form_frame, text="Ad:").grid(row=0, column=0, padx=5, pady=8, sticky="w")
entry_ad = tk.Entry(form_frame, width=22)
entry_ad.grid(row=0, column=1, padx=5, pady=8)


tk.Label(form_frame, text="Soyad:").grid(row=0, column=2, padx=5, pady=8, sticky="w")
entry_soyad = tk.Entry(form_frame, width=22)
entry_soyad.grid(row=0, column=3, padx=5, pady=8)


tk.Label(form_frame, text="Statü:").grid(row=0, column=4, padx=5, pady=8, sticky="w")
entry_statu = tk.Entry(form_frame, width=22)
entry_statu.grid(row=0, column=5, padx=5, pady=8)


btn_ekle = tk.Button(
    form_frame,
    text="Personel Ekle ve Yüz Kaydı Yap",
    command=personel_ekle,
    width=28
)
btn_ekle.grid(row=0, column=6, padx=10, pady=8)


btn_sil = tk.Button(
    form_frame,
    text="Seçili Personeli Sil",
    command=personel_sil,
    width=22
)
btn_sil.grid(row=0, column=7, padx=5, pady=8)


personel_columns = ("ID", "Ad", "Soyad", "Statü")

personel_tree = ttk.Treeview(
    personel_frame,
    columns=personel_columns,
    show="headings"
)

for c in personel_columns:
    personel_tree.heading(c, text=c)
    personel_tree.column(c, width=180)

personel_tree.pack(fill="both", expand=True, padx=10, pady=10)


# =========================
# GİRİŞ ÇIKIŞ LOG SEKİMESİ
# =========================
log_frame = ttk.Frame(notebook)
notebook.add(log_frame, text="Giriş / Çıkış Logları")


log_columns = ("ID", "Personel ID", "Ad", "Soyad", "Statü", "İşlem", "Tarih")

log_tree = ttk.Treeview(
    log_frame,
    columns=log_columns,
    show="headings"
)

for c in log_columns:
    log_tree.heading(c, text=c)
    log_tree.column(c, width=140)

log_tree.pack(fill="both", expand=True, padx=10, pady=10)


personel_tablo_guncelle()
log_tablo_guncelle()

root.mainloop()