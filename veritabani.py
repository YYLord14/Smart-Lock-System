import sqlite3
import os

DB_NAME = "fabrika.db"


def baglanti_olustur():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    return conn, cursor


def kolon_var_mi(cursor, tablo, kolon):
    cursor.execute(f"PRAGMA table_info({tablo})")
    kolonlar = cursor.fetchall()

    for bilgi in kolonlar:
        if bilgi[1] == kolon:
            return True

    return False


def tablolar_olustur():
    conn, cursor = baglanti_olustur()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS personel (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ad TEXT NOT NULL,
        soyad TEXT NOT NULL,
        statu TEXT NOT NULL,
        kayit_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS giris_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        personel_id INTEGER,
        ad TEXT,
        soyad TEXT,
        statu TEXT,
        islem TEXT,
        giris_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    if not kolon_var_mi(cursor, "giris_logs", "islem"):
        cursor.execute("""
        ALTER TABLE giris_logs
        ADD COLUMN islem TEXT DEFAULT 'GIRIS'
        """)

    conn.commit()
    conn.close()


def veritabani_baslat():
    if not os.path.exists(DB_NAME):
        print("Veritabani olusturuluyor...")

    tablolar_olustur()
    print("Veritabani hazir.")


def personel_ekle(ad, soyad, statu):
    conn, cursor = baglanti_olustur()

    cursor.execute("""
    INSERT INTO personel (ad, soyad, statu)
    VALUES (?, ?, ?)
    """, (ad, soyad, statu))

    conn.commit()
    conn.close()


def giris_log_ekle(personel_id, ad, soyad, statu, islem):
    conn, cursor = baglanti_olustur()

    cursor.execute("""
    INSERT INTO giris_logs (personel_id, ad, soyad, statu, islem, giris_zamani)
    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (personel_id, ad, soyad, statu, islem))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    veritabani_baslat()