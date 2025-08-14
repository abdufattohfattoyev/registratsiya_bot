# # database_migration_fix.py
# # Mavjud database'ni to'g'irlash uchun
#
# import sqlite3
# import os
#
#
# def fix_database_structure():
#     """Mavjud database strukturasini to'g'irlash"""
#     db_path = "db/bot_database.db"
#
#     if not os.path.exists(db_path):
#         print("❌ Database fayli topilmadi!")
#         return
#
#     conn = sqlite3.connect(db_path)
#     cursor = conn.cursor()
#
#     try:
#         print("🔧 Database strukturasini tekshiryapmiz...")
#
#         # 1. Channels jadvalidagi ustunlarni tekshirish
#         cursor.execute("PRAGMA table_info(channels)")
#         channel_columns = [column[1] for column in cursor.fetchall()]
#         print(f"Channels jadval ustunlari: {channel_columns}")
#
#         # channel_username ustuni qo'shish
#         if 'channel_username' not in channel_columns:
#             print("⚠️ channel_username ustuni yo'q, qo'shilyapti...")
#             cursor.execute("ALTER TABLE channels ADD COLUMN channel_username TEXT")
#             conn.commit()
#             print("✅ channel_username ustuni qo'shildi")
#         else:
#             print("✅ channel_username ustuni mavjud")
#
#         # 2. Events jadvalidagi ustunlarni tekshirish
#         cursor.execute("PRAGMA table_info(events)")
#         event_columns = [column[1] for column in cursor.fetchall()]
#         print(f"Events jadval ustunlari: {event_columns}")
#
#         # Agar eski struktura bo'lsa (faqat name_uz), yangi ustunlar qo'shish
#         if 'name_ru' not in event_columns:
#             print("⚠️ Ko'p tillar uchun ustunlar yo'q, qo'shilyapti...")
#             cursor.execute("ALTER TABLE events ADD COLUMN name_ru TEXT DEFAULT ''")
#             cursor.execute("ALTER TABLE events ADD COLUMN name_en TEXT DEFAULT ''")
#             cursor.execute("ALTER TABLE events ADD COLUMN address_ru TEXT DEFAULT ''")
#             cursor.execute("ALTER TABLE events ADD COLUMN address_en TEXT DEFAULT ''")
#
#             # Mavjud ma'lumotlarni yangilash
#             cursor.execute(
#                 "UPDATE events SET name_ru = name_uz, name_en = name_uz WHERE name_ru IS NULL OR name_ru = ''")
#             cursor.execute(
#                 "UPDATE events SET address_ru = address_uz, address_en = address_uz WHERE address_ru IS NULL OR address_ru = ''")
#
#             conn.commit()
#             print("✅ Ko'p til ustunlari qo'shildi va ma'lumotlar yangilandi")
#         else:
#             print("✅ Ko'p til ustunlari mavjud")
#
#         # 3. Users jadvalidagi ustunlarni tekshirish
#         cursor.execute("PRAGMA table_info(users)")
#         user_columns = [column[1] for column in cursor.fetchall()]
#         print(f"Users jadval ustunlari: {user_columns}")
#
#         # language ustuni qo'shish
#         if 'language' not in user_columns:
#             print("⚠️ language ustuni yo'q, qo'shilyapti...")
#             cursor.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'uz'")
#             conn.commit()
#             print("✅ language ustuni qo'shildi")
#         else:
#             print("✅ language ustuni mavjud")
#
#         # 4. Ma'lumotlar tozaligi tekshirish
#         cursor.execute("SELECT COUNT(*) FROM channels")
#         channels_count = cursor.fetchone()[0]
#         print(f"📊 Kanallar soni: {channels_count}")
#
#         cursor.execute("SELECT COUNT(*) FROM events")
#         events_count = cursor.fetchone()[0]
#         print(f"📊 Tadbirlar soni: {events_count}")
#
#         cursor.execute("SELECT COUNT(*) FROM users")
#         users_count = cursor.fetchone()[0]
#         print(f"📊 Foydalanuvchilar soni: {users_count}")
#
#         print("✅ Database strukturasi to'g'irlandi!")
#
#     except Exception as e:
#         print(f"❌ Xatolik: {e}")
#         conn.rollback()
#     finally:
#         conn.close()
#
#
# if __name__ == "__main__":
#     fix_database_structure()