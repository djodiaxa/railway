import telebot
import psycopg2
import os

# Mengambil variabel dari Railway Environment
TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

bot = telebot.TeleBot(TOKEN)

# Koneksi ke PostgreSQL
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# Buat tabel jika belum ada
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
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

init_db()

def get_role(xp):
    if xp >= 10000: return "Titan Lord ♱"
    elif xp >= 5000: return "Jenderal 𖤐"
    elif xp >= 2000: return "Ksatria ⚜︎"
    elif xp >= 500: return "Prajurit ⚔︎"
    else: return "Rakyat ⛏︎"

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    name = message.from_user.first_name

    if message.from_user.is_bot:
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    # Cek user di database
    cursor.execute("SELECT xp, role FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()

    if user is None:
        # User baru
        current_xp = 10
        current_role = "Rakyat ⛏︎"
        cursor.execute("INSERT INTO users (user_id, xp, role) VALUES (%s, %s, %s)", (user_id, current_xp, current_role))
    else:
        # Update XP user lama
        current_xp = user[0] + 10
        current_role = user[1]
        cursor.execute("UPDATE users SET xp = %s WHERE user_id = %s", (current_xp, user_id))

    new_role = get_role(current_xp)

    # Jika ada kenaikan pangkat
    if current_role != new_role:
        cursor.execute("UPDATE users SET role = %s WHERE user_id = %s", (new_role, user_id))
        
        try:
            bot.set_chat_member_tag(chat_id, user_id, tag=new_role)
            bot.reply_to(message, f"🎉 Luar biasa! {name} telah naik level menjadi **{new_role}** di Empire of Titan!")
        except Exception as e:
            print(f"Gagal mengubah peran: {e}")

    conn.commit()
    cursor.close()
    conn.close()

print("Bot Empire of Titan menyala...")
bot.polling(none_stop=True)
