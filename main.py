import telebot
import psycopg2
import os

# Mengambil variabel token dan database dari pengaturan Railway
TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

bot = telebot.TeleBot(TOKEN)

# ==========================================
# KONFIGURASI DATABASE
# ==========================================
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Membuat tabel jika belum ada saat bot pertama kali menyala
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            xp INT DEFAULT 0,
            role TEXT DEFAULT 'Rakyat ⛏︎'
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

# Jalankan inisialisasi database
init_db()

# ==========================================
# LOGIKA PANGKAT (Sesuai Limit 16 Karakter Telegram)
# ==========================================
def get_role(xp):
    if xp >= 10000: return "Titan Lord ♱"
    elif xp >= 5000: return "Jenderal 𖤐"
    elif xp >= 2000: return "Ksatria ⚜︎"
    elif xp >= 500: return "Prajurit ⚔︎"
    else: return "Rakyat ⛏︎"

# ==========================================
# HANDLER PERINTAH (COMMANDS)
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "⚔️ Selamat datang di Empire of Titan!\n\nBot sudah aktif. Teruslah mengobrol di grup untuk mengumpulkan XP dan raih pangkat tertinggi!")

@bot.message_handler(commands=['profil'])
def check_profile(message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT xp, role FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        xp = user[0]
        role = user[1]
        bot.reply_to(message, f"🏰 **Buku Induk Kekaisaran** 🏰\n\n👤 Nama: {name}\n⚜️ Pangkat: {role}\n💠 Total XP: {xp}", parse_mode="Markdown")
    else:
        bot.reply_to(message, "Kamu belum terdaftar di kekaisaran. Kirim satu pesan apa saja di grup untuk mulai mengumpulkan XP!")

# ==========================================
# HANDLER CHAT UTAMA (SISTEM XP)
# ==========================================
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    name = message.from_user.first_name

    # Jangan beri XP ke bot lain atau bot ini sendiri
    if message.from_user.is_bot:
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    # Cek apakah user sudah ada di database
    cursor.execute("SELECT xp, role FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()

    if user is None:
        # Tambah user baru (Langsung dapat 10 XP untuk chat pertama)
        current_xp = 10
        current_role = "Rakyat ⛏︎"
        cursor.execute("INSERT INTO users (user_id, xp, role) VALUES (%s, %s, %s)", (user_id, current_xp, current_role))
    else:
        # Tambah 10 XP untuk user lama
        current_xp = user[0] + 10
        current_role = user[1]
        cursor.execute("UPDATE users SET xp = %s WHERE user_id = %s", (current_xp, user_id))

    # Cek apakah XP yang baru mencapai batas naik pangkat
    new_role = get_role(current_xp)

    # Eksekusi jika terjadi perubahan pangkat
    if current_role != new_role:
        cursor.execute("UPDATE users SET role = %s WHERE user_id = %s", (new_role, user_id))
        
        try:
            # Fungsi API Telegram terbaru untuk mengubah peran/tag anggota
            bot.set_chat_member_tag(chat_id, user_id, tag=new_role)
            bot.reply_to(message, f"🎉 Luar biasa! **{name}** telah naik level menjadi **{new_role}** di Empire of Titan!", parse_mode="Markdown")
        except AttributeError:
            # Fallback (Jaga-jaga jika versi pyTelegramBotAPI di server belum update)
            telebot.apihelper.method_request(TOKEN, 'setChatMemberTag', {'chat_id': chat_id, 'user_id': user_id, 'tag': new_role})
            bot.reply_to(message, f"🎉 Luar biasa! **{name}** telah naik level menjadi **{new_role}** di Empire of Titan!", parse_mode="Markdown")
        except Exception as e:
            print(f"Gagal mengubah peran di grup: {e}")

    # Simpan perubahan dan tutup koneksi database
    conn.commit()
    cursor.close()
    conn.close()

# ==========================================
# JALANKAN BOT
# ==========================================
print("Bot Empire of Titan menyala...")
bot.polling(none_stop=True)
        
