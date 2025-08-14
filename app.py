from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from data import config
from handlers.users.start import register_user_handlers
from handlers.users.admin import register_admin_handlers
from utils.db_api.database import Database
from middlewares.subscription_middleware import SubscriptionMiddleware

# Google Sheets import
GOOGLE_SHEETS_ENABLED = False
try:
    from sheets_integration import init_google_sheets, get_sheets_url
    GOOGLE_SHEETS_ENABLED = True
    print("✅ Google Sheets (sheets_integration) integratsiyasi yoqildi")
except ImportError as e:
    print(f"⚠️ Google Sheets import xatolik: {e}")
    GOOGLE_SHEETS_ENABLED = False

# Bot va dispatcher
bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(SubscriptionMiddleware())

# Database — faqat bir marta yaratiladi
db = Database()


async def on_startup(dispatcher):
    """Bot ishga tushganda bajariladigan funksiya"""
    global GOOGLE_SHEETS_ENABLED
    print("🚀 Bot ishga tushmoqda...")
    print("=" * 50)

    # Ma'lumotlar bazasini ishga tushirish
    print("🔧 Ma'lumotlar bazasini ishga tushirish...")
    try:
        print("✅ Ma'lumotlar bazasi tayyor!")
        stats = db.get_all_user_stats()
        print(f"📊 Bazada {stats['total']} foydalanuvchi mavjud")
        print(f"   - Tasdiqlangan: {stats['approved']}")
        print(f"   - Kutilayotgan: {stats['pending']}")
    except Exception as e:
        print(f"❌ Ma'lumotlar bazasi ishga tushirishda xatolik: {e}")
        import traceback
        traceback.print_exc()
        return

    # Google Sheets ni ishga tushirish
    if GOOGLE_SHEETS_ENABLED:
        print(f"\n🔄 Google Sheets ni ishga tushirish...")
        try:
            credentials_file = getattr(config, 'GOOGLE_CREDENTIALS_FILE', 'credentials.json')
            spreadsheet_id = getattr(config, 'SPREADSHEET_ID', None)
            sheets_success = init_google_sheets(
                credentials_path=credentials_file,
                spreadsheet_id=spreadsheet_id
            )
            if sheets_success:
                print("✅ Google Sheets muvaffaqiyatli ishga tushdi!")
                sheets_url = get_sheets_url()
                if sheets_url:
                    print(f"📊 Jadval URL: {sheets_url}")
                    print("📝 QR kodlar ID sifatida saqlanadi")
            else:
                print("❌ Google Sheets ishlamadi")
                GOOGLE_SHEETS_ENABLED = False
        except Exception as e:
            print(f"❌ Google Sheets ishga tushirishda xatolik: {e}")
            print("⚠️ Bot Google Sheets bo'lmasdan ham to'liq ishlaydi")
            GOOGLE_SHEETS_ENABLED = False
    else:
        print("⚠️ Google Sheets o'chiq - faqat mahalliy ma'lumotlar bazasi")

    # Handlerlarni ro'yxatdan o'tkazish
    print("\n🔧 Handlerlarni ro'yxatdan o'tkazish...")
    try:
        register_user_handlers(dp)
        register_admin_handlers(dp)
        print("✅ Barcha handlerlar muvaffaqiyatli ro'yxatdan o'tdi!")
    except Exception as e:
        print(f"❌ Handlerlarni ro'yxatga olishda xatolik: {e}")
        import traceback
        traceback.print_exc()
        return

    # Admin ma'lumotlari
    print(f"\n👨‍💼 Admin IDs: {config.ADMINS}")

    # Startup xabari
    print("\n" + "=" * 50)
    print("🎉 BOT TO'LIQ ISHGA TUSHDI!")
    print("=" * 50)
    print("\n📋 MAVJUD FUNKSIYALAR:")
    print("   🔧 Admin panel: /admin")
    print("   📱 QR skaner: Admin panel > QR Skaner")
    if GOOGLE_SHEETS_ENABLED:
        print(f"   📊 Google Sheets: Admin panel > Google Sheets")
    print("   👥 Foydalanuvchi boshqaruvi")
    print("   📈 Kelganlik statistikasi")
    print("   🎫 QR kod yaratish va skanerlash")

    print("\n🔗 TEZKOR HAVOLALAR:")
    try:
        if GOOGLE_SHEETS_ENABLED:
            sheets_url = get_sheets_url()
            if sheets_url:
                print(f"   📊 Google Sheets: {sheets_url}")
    except:
        pass

    try:
        bot_info = await bot.get_me()
        print(f"   🤖 Bot: @{bot_info.username}")
    except Exception as e:
        print(f"   🤖 Bot: {e}")

    print("\n✅ Bot foydalanishga tayyor!")


async def on_shutdown(dispatcher):
    """Bot to'xtatilganda bajariladigan funksiya"""
    print("\n🛑 Bot to'xtatilmoqda...")
    try:
        backup_path = db.backup_database()
        if backup_path:
            print(f"💾 Ma'lumotlar bazasi zahiralandi: {backup_path}")
    except Exception as e:
        print(f"❌ Zahiralashda xatolik: {e}")
    print("👋 Bot muvaffaqiyatli to'xtatildi!")


if __name__ == '__main__':
    try:
        print("🔄 BOT ISHGA TUSHIRILMOQDA...")
        print("=" * 50)
        print(f"🤖 Bot Token: {'✅ Mavjud' if config.BOT_TOKEN else '❌ Yo`q'}")
        print(f"👨‍💼 Admin raqamlar: {config.ADMINS}")
        credentials_file = getattr(config, 'GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        print(f"🗂 Google Credentials: {credentials_file}")
        spreadsheet_id = getattr(config, 'SPREADSHEET_ID', None)
        if spreadsheet_id:
            print(f"📊 Spreadsheet ID: {spreadsheet_id}")
        else:
            print("📊 Spreadsheet ID: Avtomatik yaratiladi")
        print("=" * 50)
        executor.start_polling(
            dp,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Bot foydalanuvchi tomonidan to'xtatildi!")
    except Exception as e:
        print(f"\n❌ KRITIK XATOLIK: {e}")
        import traceback
        traceback.print_exc()
        print("🔧 Iltimos quyidagilarni tekshiring:")
        print("   - BOT_TOKEN to'g'riligini")
        print("   - Google credentials faylini")
        print("   - Internet ulanishini")
        print("   - Kerakli kutubxonalar o'rnatilganligini")
    finally:
        print("\n👋 Dastur tugadi!")
