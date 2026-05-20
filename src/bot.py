print("🔥 IMANUEL Bot - Full Version Lengkap")

import telebot
from telebot import types
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv(override=True)

TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID")) if os.getenv("ADMIN_ID") else None

if not TOKEN:
    print("❌ TOKEN tidak ditemukan di .env!")
    exit()
if not ADMIN_ID:
    print("⚠️ ADMIN_ID belum diatur di .env")

bot = telebot.TeleBot(TOKEN)
user_states = {}

# Import Database
from database import (
    tambah_permintaan, get_all_data, update_kembali, 
    export_to_excel, approve_pinjam, reject_pinjam, 
    hapus_data, hapus_semua_data
)

# AI Setup
client = None
handle_tanya_bebas = None
try:
    from groq import Groq
    from ai_handler import handle_tanya_bebas as ai_func
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    handle_tanya_bebas = ai_func
    print("✅ AI Active")
except:
    print("⚠️ AI Offline")

def build_keyboard(is_admin=False):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    if is_admin:
        markup.add('📋 Lihat Data', '➕ Minta Pinjam')
        markup.add('🔄 Ubah Status', '📊 Cetak Data')
        markup.add('🗑️ Hapus Laporan', '🤖 Tanya AI')
        markup.add('ℹ️ Bantuan')
    else:
        markup.add('➕ Ajukan Peminjaman')
        markup.add('ℹ️ Bantuan')
    
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    is_admin = (message.from_user.id == ADMIN_ID)
    welcome = "👋 Selamat datang di Peminjaman Laptop SMKIT IF!" if not is_admin else "👋 Halo Admin!"
    bot.reply_to(message, welcome, reply_markup=build_keyboard(is_admin))

# ====================== AJUKAN PEMINJAMAN ======================
@bot.message_handler(func=lambda m: m.text in ['➕ Ajukan Peminjaman', '➕ Minta Pinjam'])
def minta_pinjam_start(message):
    user_states[message.from_user.id] = {'step': 'nama'}
    bot.reply_to(message, "👤 Nama lengkap peminjam:")

# ====================== MAIN HANDLER ======================
@bot.message_handler(func=lambda m: True)
def main_handler(message):
    uid = message.from_user.id
    is_admin = (uid == ADMIN_ID)
    state = user_states.get(uid)

    # AI Mode (hanya admin)
    if state == 'ai_mode':
        if not is_admin:
            return bot.reply_to(message, "❌ Fitur ini hanya untuk admin.")
        if message.text.lower() in ['keluar', 'menu', '/keluar']:
            user_states.pop(uid, None)
            return bot.reply_to(message, "✅ Keluar dari mode AI.", reply_markup=build_keyboard(is_admin))
        try:
            bot.reply_to(message, "🤖 IMANUEL berpikir...")
            jawab = handle_tanya_bebas(message.text, client)
            bot.reply_to(message, jawab)
        except:
            bot.reply_to(message, "❌ AI error.")
        return

    # ==================== FLOW AJUKAN PEMINJAMAN ====================
    if isinstance(state, dict):
        step = state.get('step')

        if step == 'nama':
            nama = message.text.strip()
            user_states[uid] = {'step': 'kelas', 'nama': nama}
            bot.reply_to(message, f"✅ Nama: *{nama}*\n\n🏫 Masukkan kelas:", parse_mode='Markdown')
            return

        elif step == 'kelas':
            user_states[uid] = {'step': 'izin', 'nama': state['nama'], 'kelas': message.text.upper()}
            bot.reply_to(message, "👨‍🏫 Atas izin siapa?")
            return

        elif step == 'izin':
            user_states[uid] = {'step': 'keperluan', 'nama': state['nama'], 'kelas': state['kelas'], 'izin_dari': message.text.strip()}
            bot.reply_to(message, "📝 Keperluan / Alasan meminjam laptop?")
            return

        elif step == 'keperluan':
            user_states[uid] = {
                'step': 'tanggal_kembali',
                'nama': state['nama'],
                'kelas': state['kelas'],
                'izin_dari': state['izin_dari'],
                'keperluan': message.text.strip()
            }
            bot.reply_to(message, "📅 Kapan tanggal kembali yang diharapkan?\n(contoh: 2026-05-25)")
            return

        elif step == 'tanggal_kembali':
            nama = state['nama']
            kelas = state['kelas']
            izin_dari = state['izin_dari']
            keperluan = state['keperluan']
            tgl_kembali = message.text.strip()

            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✅ Kirim Permintaan", callback_data=f"confirm|{nama}|{kelas}|{izin_dari}|{keperluan}|{tgl_kembali}"))
            markup.add(types.InlineKeyboardButton("❌ Batal", callback_data="cancel"))

            bot.reply_to(message, f"""*Konfirmasi Permintaan Pinjam*

👤 Nama     : {nama}
🏫 Kelas    : {kelas}
👨‍🏫 Izin    : {izin_dari}
📝 Alasan   : {keperluan}
📅 Pengembalian : {tgl_kembali}

Apakah sudah benar?""", parse_mode='Markdown', reply_markup=markup)
            user_states.pop(uid, None)
            return

    # ==================== MENU ADMIN ====================
    if is_admin:
        if message.text == '📋 Lihat Data':
            data = get_all_data()
            text = "📊 *DAFTAR PEMINJAMAN*\n\n"
            for row in data:
                # Menggunakan tag HTML <b> untuk tebal, dan <i> untuk miring
                text += f"👤 <b>{row[1]}</b> ({row[2]}) — <i>{row[7]}</i>\n"
                text += f"📅 Pinjam: {row[3]}\n"
                text += f"📅 Pengembalian : {row[4]}\n"
                text += f"📝 {row[6]}\n\n"

            # Ubah parse_mode menjadi 'HTML'
            bot.reply_to(message, text if data else "📂 Kosong", parse_mode='HTML')

        elif message.text == '📊 Cetak Data':
            filename = export_to_excel()
            if filename:
                with open(filename, 'rb') as f:
                    bot.send_document(message.chat.id, f, caption="📄 Data Peminjaman")
                os.remove(filename)
            else:
                bot.reply_to(message, "Tidak ada data.")

        elif message.text == '🔄 Ubah Status':
            user_states[uid] = {'step': 'ubah_nama'}
            bot.reply_to(message, "👤 Nama yang mengembalikan:")

        elif message.text == '🗑️ Hapus Laporan':
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("🗑️ Hapus SEMUA Laporan", callback_data="hapus_semua"))
            markup.add(types.InlineKeyboardButton("🗑️ Hapus Satu-satu", callback_data="hapus_pilih"))
            bot.reply_to(message, "Pilih jenis penghapusan:", reply_markup=markup)

    # Tanya AI hanya admin
    if message.text == '🤖 Tanya AI':
        if not is_admin:
            return bot.reply_to(message, "❌ Fitur ini hanya untuk admin.")
        user_states[uid] = 'ai_mode'
        bot.reply_to(message, "💭 Mode AI aktif.\nKetik `keluar` untuk kembali.")

    elif message.text == 'ℹ️ Bantuan':
        bot.reply_to(message, "Gunakan tombol menu di bawah.")

    else:
        bot.reply_to(message, "👇 Gunakan tombol menu di bawah.", reply_markup=build_keyboard(is_admin))

# ====================== CALLBACK ======================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        if call.data == "cancel":
            bot.answer_callback_query(call.id, "❌ Dibatalkan")
            bot.edit_message_text("✅ Permintaan dibatalkan.", call.message.chat.id, call.message.message_id)
            return

        if call.data.startswith("confirm|"):
            _, nama, kelas, izin_dari, keperluan, tgl_kembali = call.data.split("|", 5)
            if tambah_permintaan(nama, kelas, izin_dari, keperluan, tgl_kembali):
                bot.answer_callback_query(call.id, "✅ Terkirim!")
                bot.edit_message_text(f"✅ Permintaan terkirim!\n👤 {nama} - {kelas}", 
                                    call.message.chat.id, call.message.message_id)

                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(types.InlineKeyboardButton("✅ Setujui", callback_data=f"approve|{nama}|{kelas}"))
                markup.add(types.InlineKeyboardButton("❌ Tolak", callback_data=f"reject|{nama}|{kelas}"))
                bot.send_message(ADMIN_ID, f"""🔔 *PERMINTAAN BARU*

👤 {nama}
🏫 {kelas}
👨‍🏫 Izin : {izin_dari}
📝 Alasan : {keperluan}
📅 Pengembalian : {tgl_kembali}""", parse_mode='Markdown', reply_markup=markup)
            return

               # ================= APPROVE =================
        if call.data.startswith("approve|"):
            _, nama, kelas = call.data.split("|")
            if approve_pinjam(nama, kelas):
                bot.answer_callback_query(call.id, "✅ Disetujui!")
                bot.edit_message_text(f"✅ {nama} - {kelas} telah DISETUJUI", 
                                    call.message.chat.id, call.message.message_id)
            else:
                bot.answer_callback_query(call.id, "❌ Gagal menyetujui")

        # ================= REJECT =================
        if call.data.startswith("reject|"):
            _, nama, kelas = call.data.split("|")
            if reject_pinjam(nama, kelas):
                bot.answer_callback_query(call.id, "❌ Ditolak!")
                bot.edit_message_text(f"❌ {nama} - {kelas} telah DITOLAK", 
                                    call.message.chat.id, call.message.message_id)
            else:
                bot.answer_callback_query(call.id, "❌ Gagal menolak")
        # Hapus Laporan
        if call.data == "hapus_semua":
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✅ Ya, Hapus SEMUA", callback_data="hapus_semua_confirm"))
            markup.add(types.InlineKeyboardButton("❌ Batal", callback_data="cancel"))
            bot.edit_message_text("⚠️ YAKIN menghapus **SEMUA** laporan?", call.message.chat.id, call.message.message_id, reply_markup=markup)

        if call.data == "hapus_semua_confirm":
            if hapus_semua_data():
                bot.answer_callback_query(call.id, "🗑️ Semua dihapus!")
                bot.edit_message_text("🧹 Semua laporan telah dihapus.", call.message.chat.id, call.message.message_id)
            else:
                bot.answer_callback_query(call.id, "❌ Gagal")

        if call.data == "hapus_pilih":
            data = get_all_data()
            markup = types.InlineKeyboardMarkup(row_width=1)
            for row in data[:20]:
                markup.add(types.InlineKeyboardButton(f"🗑️ {row[1]} ({row[2]})", callback_data=f"hapus_satu|{row[0]}"))
            bot.edit_message_text("Pilih laporan yang ingin dihapus:", call.message.chat.id, call.message.message_id, reply_markup=markup)

        if call.data.startswith("hapus_satu|"):
            data_id = int(call.data.split("|")[1])
            if hapus_data(data_id):
                bot.answer_callback_query(call.id, "✅ Dihapus")
                bot.edit_message_text("✅ Laporan berhasil dihapus.", call.message.chat.id, call.message.message_id)

    except Exception as e:
        print("Callback Error:", e)

print("🚀 IMANUEL Bot Full Version aktif!")
bot.infinity_polling()