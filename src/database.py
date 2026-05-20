# database.py
import sqlite3
from datetime import datetime
import pandas as pd

DB_NAME = "peminjaman_laptop.db"

# ================= INIT DATABASE =================
def init_db():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS peminjaman (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            kelas TEXT NOT NULL,
            tanggal_pinjam TEXT,
            tanggal_kembali_diharapkan TEXT,
            tanggal_kembali TEXT,
            keterangan TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database SQLite berhasil diinisialisasi")


# ================= TAMBAH PERMINTAAN =================
def tambah_permintaan(nama, kelas, izin_dari, keperluan, tanggal_kembali_diharapkan):
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        c = conn.cursor()

        tanggal_pinjam = datetime.now().strftime("%Y-%m-%d %H:%M")
        keterangan_full = f"Izin: {izin_dari} | Keperluan: {keperluan}"

        c.execute("""
            INSERT INTO peminjaman 
            (nama, kelas, tanggal_pinjam, tanggal_kembali_diharapkan, keterangan, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nama, kelas, tanggal_pinjam, tanggal_kembali_diharapkan, keterangan_full, "Pending"))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("ERROR tambah_permintaan:", e)
        return False


# ================= GET ALL DATA =================
def get_all_data():
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        c = conn.cursor()
        c.execute("SELECT * FROM peminjaman ORDER BY id DESC")
        data = c.fetchall()
        conn.close()
        return data
    except Exception as e:
        print("ERROR get_all_data:", e)
        return []


# ================= APPROVE =================
def approve_pinjam(nama, kelas):
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        c = conn.cursor()
        c.execute("""
            UPDATE peminjaman 
            SET status = 'Approved' 
            WHERE nama = ? AND kelas = ? AND status = 'Pending'
        """, (nama, kelas))
        success = c.rowcount > 0
        conn.commit()
        conn.close()
        return success
    except Exception as e:
        print("ERROR approve_pinjam:", e)
        return False


# ================= REJECT =================
def reject_pinjam(nama, kelas):
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        c = conn.cursor()
        c.execute("""
            DELETE FROM peminjaman 
            WHERE nama = ? AND kelas = ? AND status = 'Pending'
        """, (nama, kelas))
        success = c.rowcount > 0
        conn.commit()
        conn.close()
        return success
    except Exception as e:
        print("ERROR reject_pinjam:", e)
        return False


# ================= HAPUS SATU DATA =================
def hapus_data(data_id):
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        c = conn.cursor()
        c.execute("DELETE FROM peminjaman WHERE id = ?", (data_id,))
        success = c.rowcount > 0
        conn.commit()
        conn.close()
        return success
    except Exception as e:
        print("ERROR hapus_data:", e)
        return False


# ================= HAPUS SEMUA DATA =================
def hapus_semua_data():
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        c = conn.cursor()
        c.execute("DELETE FROM peminjaman")
        conn.commit()
        conn.close()
        print("✅ Semua data berhasil dihapus dari database")
        return True
    except Exception as e:
        print("ERROR hapus_semua_data:", e)
        return False


# ================= UPDATE KEMBALI =================
def update_kembali(nama, kelas):
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        c = conn.cursor()
        tanggal_kembali = datetime.now().strftime("%Y-%m-%d %H:%M")

        c.execute("""
            UPDATE peminjaman
            SET tanggal_kembali = ?,
                status = 'Sudah Kembali'
            WHERE nama = ? AND kelas = ? AND tanggal_kembali IS NULL
        """, (tanggal_kembali, nama, kelas))

        success = c.rowcount > 0
        conn.commit()
        conn.close()
        return success
    except Exception as e:
        print("ERROR update_kembali:", e)
        return False


# ================= EXPORT TO EXCEL =================
def export_to_excel():
    try:
        data = get_all_data()
        if not data:
            return None

        df = pd.DataFrame(data, columns=[
            "ID", "Nama", "Kelas", "Tanggal Pinjam", 
            "Tanggal Kembali Diharapkan", "Tanggal Kembali", 
            "Keterangan", "Status"
        ])

        filename = f"data_peminjaman_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(filename, index=False)
        return filename
    except Exception as e:
        print("ERROR export_to_excel:", e)
        return None


# ================= AUTO INIT =================
init_db()