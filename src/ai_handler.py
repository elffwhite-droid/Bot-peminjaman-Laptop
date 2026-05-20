# ai_handler.py

from database import get_all_data

def handle_tanya_bebas(perintah: str, client):
    try:
        data = get_all_data()
        konteks = []

        # Fungsi untuk menghitung total pinjam siswa dari seluruh database
        def hitung_total_pinjam(nama_siswa):
            return sum(1 for r in data if r[1].lower() == nama_siswa.lower())

        # Mengambil 15 data terbaru agar AI punya konteks yang cukup
        for row in data[:15]:
            try:
                nama = row[1]
                kelas = row[2]
                tgl_pinjam = row[3]
                janji_kembali = row[4]
                keterangan_full = row[6] # Format asli: "Izin: Pak Budi | Keperluan: Tugas"
                
                # Memisahkan status izin dan keperluan agar AI tahu siapa izin ke siapa
                info_izin = "Tidak ada data izin"
                info_keperluan = keterangan_full
                
                if " | " in keterangan_full:
                    parts = keterangan_full.split(" | ")
                    info_izin = parts[0]       # Mengambil "Izin: Nama Guru"
                    info_keperluan = parts[1]  # Mengambil "Keperluan: Alasan"

                total_pinjam = hitung_total_pinjam(nama)

                # Masukkan semua data penting termasuk informasi izin ke konteks AI
                konteks.append(
                    f"• Siswa: {nama} ({kelas}) | {info_izin}\n"
                    f"  Total Pinjam: {total_pinjam}x\n"
                    f"  Pinjam: {tgl_pinjam} | Janji Kembali: {janji_kembali}\n"
                    f"  {info_keperluan}"
                )
            except IndexError:
                continue

        konteks_text = "\n\n".join(konteks) if konteks else "Tidak ada data peminjaman."

        prompt = f"""
Kamu adalah IMANUEL, AI asisten peminjaman laptop sekolah.

DATA PEMINJAMAN TERBARU:
{konteks_text}

Pertanyaan User:
{perintah}

Jawab:
ATURAN WAJIB:
Gunakan aturan indikator ini untuk menganalisis kelayakan (perhatikan kesesuaian antara guru yang memberi izin, keperluan, dan tanggal janji pengembalian):
🟢 AMAN: Peminjaman wajar, frekuensi sedikit, alasan logis, izin dari guru jelas.
🟡 PANTAU: Alasan mulai diulang-ulang, janji kembali terlalu lama, atau tugas belum selesai lewat dari batas wajar.
🔴 CURIGA: Frekuensi terlalu sering, nama guru pemberi izin mencurigakan/palsu, alasan aneh, atau indikasi dipakai main game/pribadi.

--------------------------------------------------
WAJIB IKUTI FORMAT RINGKAS INI (Jangan buat teks panjang!):

[🟢/🟡/🔴] [NAMA] ([KELAS]) -> [Total: X kali pinjam]
• Masalah: [Tulis 1 kalimat pendek saja jika ada kejanggalan/keterlambatan/keanehan izin. Jika aman, tulis "Normal".]
• Solusi: [Tulis 1 saran tindakan singkat dan tegas untuk guru.]

--------------------------------------------------
"""
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=300
        )

        return completion.choices[0].message.content

    except Exception as e:
        print("[AI ERROR]", e)
        return f"❌ AI Error\n\n{e}"
