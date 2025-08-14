
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from data import config
from keyboards.default.keyboards import (
    get_main_menu,
    get_payment_confirmation_keyboard,
    get_event_selection_menu,
    get_subscribe_button,
    get_contact_keyboard,
    get_language_keyboard,
    get_change_language_keyboard,
    get_user_info_keyboard,
    get_back_to_main_keyboard, get_admin_approval_keyboard,
)
from loader import db
from utils.db_api.database import Database

# Google Sheets import
try:
    from sheets_integration import save_user_with_qr_to_sheets

    SHEETS_MODE = True
    print("✅ Google Sheets user handlers da ulanadi")
except ImportError:
    SHEETS_MODE = False
    print("❌ Google Sheets user handlers da ulanmadi")


# User states
class UserStates(StatesGroup):
    waiting_for_language = State()
    waiting_for_obuna = State()
    waiting_for_contact = State()
    waiting_for_full_name = State()  # Yangi holat
    waiting_for_payment_screenshot = State()


async def check_user_subscription(bot, user_id, channels):
    """
    TUZATILGAN: Foydalanuvchi barcha kerakli kanallarga obuna bo'lganligini tekshiradi.
    channels -> [(channel_id, channel_name, channel_username, channel_type), ...]
    """
    try:
        if not channels:
            print("📝 Hech qanday kanal topilmadi")
            return True  # Kanal yo'q bo'lsa, obuna tekshirish shart emas

        for channel in channels:
            try:
                # Channel tuple dan ma'lumotlarni olish
                channel_id, channel_name, channel_username, channel_type = channel

                # Actual channel identifier ni aniqlash
                if channel_id.startswith('@'):
                    # Public channel username
                    actual_channel_id = channel_id
                    print(f"🔍 Tekshirilayotgan kanal (username): {actual_channel_id}")
                elif channel_id.startswith('-100'):
                    # Private channel ID
                    actual_channel_id = int(channel_id)
                    print(f"🔍 Tekshirilayotgan kanal (ID): {actual_channel_id}")
                elif channel_id.isdigit() or (channel_id.startswith('-') and channel_id[1:].isdigit()):
                    # Numeric ID
                    actual_channel_id = int(channel_id)
                    print(f"🔍 Tekshirilayotgan kanal (numeric): {actual_channel_id}")
                else:
                    print(f"⚠️ Noma'lum kanal format: {channel_id}")
                    continue  # Skip invalid format

                # Bot API orqali obuna tekshirish
                member = await bot.get_chat_member(actual_channel_id, user_id)

                if member.status not in ["member", "administrator", "creator"]:
                    print(f"🚫 User {user_id} kanalga obuna emas: {actual_channel_id} (status: {member.status})")
                    return False
                else:
                    print(f"✅ User {user_id} kanalga obuna: {actual_channel_id}")

            except Exception as channel_error:
                print(f"❌ Kanal {channel_id} tekshirishda xatolik: {channel_error}")
                # Agar kanal mavjud bo'lmasa yoki bot unga kira olmasa, False qaytarish
                return False

        print(f"✅ User {user_id} barcha kanallarga obuna!")
        return True

    except Exception as e:
        print(f"❌ check_user_subscription da umumiy xatolik: {e}")
        return False



def get_status_message(status, lang):
    """Get user registration status message based on language."""
    messages = {
        'pending': {
            'uz': "💳 To'lov kutilmoqda",
            'ru': "💳 Ожидается оплата",
            'en': "💳 Payment pending"
        },
        'pending_approval': {
            'uz': "⏳ Admin tekshiruvi kutilmoqda",
            'ru': "⏳ Ожидается проверка админа",
            'en': "⏳ Waiting for admin approval"
        },
        'approved': {
            'uz': "✅ Tasdiqlangan",
            'ru': "✅ Подтверждено",
            'en': "✅ Approved"
        },
        'rejected': {
            'uz': "❌ Rad etilgan",
            'ru': "❌ Отклонено",
            'en': "❌ Rejected"
        },
        'not_registered': {
            'uz': "📝 Ro'yxatdan o'tmagan",
            'ru': "📝 Не зарегистрирован",
            'en': "📝 Not registered"
        }
    }
    return messages.get(status, {}).get(lang, f"Status: {status}")


async def start_handler(message: types.Message, state: FSMContext):
    """TUZATILGAN /start command handler."""
    try:
        db = Database()
        user_id = message.from_user.id

        # Clear state
        await state.finish()

        # Get user from database
        user = db.get_user(user_id)
        lang = user[13] if user and len(user) > 13 and user[13] else 'uz'

        # 1️⃣ First check channel subscriptions
        channels = db.get_all_channels()
        print(f"📋 Topilgan kanallar: {len(channels)} ta")

        if channels:
            print(f"🔍 Kanallar ro'yxati: {channels}")
            subscribed = await check_user_subscription(message.bot, user_id, channels)
            print(f"📊 Obuna holati: {subscribed}")

            if not subscribed:
                texts = {
                    'uz': "📢 Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
                    'ru': "📢 Подпишитесь на следующие каналы для использования бота:",
                    'en': "📢 Subscribe to the following channels to use the bot:"
                }
                await message.answer(
                    texts.get(lang, texts['uz']),
                    reply_markup=get_subscribe_button(channels, lang)
                )
                await UserStates.waiting_for_obuna.set()
                return

        # 2️⃣ If user exists and has complete registration (name AND phone)
        if user and user[2] and user[3] and user[2] != '' and user[3] != '':
            # User is fully registered, show main menu
            welcome_texts = {
                'uz': f"👋 Assalomu alaykum, {user[2]}!",
                'ru': f"👋 Здравствуйте, {user[2]}!",
                'en': f"👋 Hello, {user[2]}!"
            }
            status = db.get_user_registration_status(user_id)
            status_msg = get_status_message(status['status'], lang)

            await message.answer(
                welcome_texts.get(lang, welcome_texts['uz']) + "\n\n" + status_msg,
                reply_markup=get_main_menu(lang)
            )
            return

        # 3️⃣ If user exists but missing name or phone (incomplete registration)
        if user:
            # User exists in database but incomplete registration
            if not user[2] or user[2] == '':
                # Missing full name
                contact_texts = {
                    'uz': "📝 Ro'yxatdan o'tishni davom ettirish uchun ism va familiyangizni kiriting (masalan: Aziz Azizov):",
                    'ru': "📝 Для продолжения регистрации введите ваше имя и фамилию (например: Aziz Azizov):",
                    'en': "📝 To continue registration, enter your first and last name (e.g., Aziz Azizov):"
                }
                await message.answer(contact_texts.get(lang, contact_texts['uz']))
                await UserStates.waiting_for_full_name.set()
                return

            if not user[3] or user[3] == '':
                # Missing phone number
                contact_texts = {
                    'uz': "📱 Ro'yxatdan o'tishni davom ettirish uchun telefon raqamingizni yuboring:",
                    'ru': "📱 Для продолжения регистрации отправьте ваш номер телефона:",
                    'en': "📱 To continue registration, send your phone number:"
                }
                await message.answer(
                    contact_texts.get(lang, contact_texts['uz']),
                    reply_markup=get_contact_keyboard(lang)
                )
                await UserStates.waiting_for_contact.set()
                return

        # 4️⃣ If no user exists OR no language selected (completely new user)
        if not user or not user[13] or str(user[13]).strip() == '':
            await message.answer(
                "🌐 Tilni tanlang / Выберите язык / Select language:",
                reply_markup=get_language_keyboard()
            )
            await UserStates.waiting_for_language.set()
            return

        # 5️⃣ This should not happen, but fallback to registration
        contact_texts = {
            'uz': "📝 Ism va familiyangizni kiriting (masalan: Aziz Azizov):",
            'ru': "📝 Введите ваше имя и фамилию (например: Aziz Azizov):",
            'en': "📝 Enter your first and last name (e.g., Aziz Azizov):"
        }
        await message.answer(contact_texts.get(lang, contact_texts['uz']))
        await UserStates.waiting_for_full_name.set()

    except Exception as e:
        print(f"❌ Start handler xatolik: {e}")
        import traceback
        traceback.print_exc()
        await message.answer("❌ Xatolik yuz berdi. Qayta /start bosing.")


async def select_language_callback(callback: types.CallbackQuery, state: FSMContext):
    """TUZATILGAN til tanlash callback."""
    try:
        lang = callback.data.split('_')[1]  # Handles 'lang_uz'
        db = Database()
        user_id = callback.from_user.id

        # Save language
        success = db.set_user_language(user_id, lang)
        if not success:
            await callback.answer("❌ Xatolik!", show_alert=True)
            return

        lang_names = {
            'uz': "O'zbek tili",
            'ru': "Русский язык",
            'en': "English"
        }
        await callback.answer(f"✅ {lang_names.get(lang, lang)}")

        # Clear state
        await state.finish()

        # Delete previous message
        await callback.message.delete()

        # Check channels
        channels = db.get_all_channels()
        print(f"📋 Til tanlagandan keyin kanallar: {len(channels)} ta")

        if channels:
            print(f"🔍 Kanallar ro'yxati: {channels}")
            subscribed = await check_user_subscription(callback.bot, user_id, channels)
            print(f"📊 Obuna holati: {subscribed}")

            if not subscribed:
                texts = {
                    'uz': "📢 Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
                    'ru': "📢 Подпишитесь на следующие каналы для использования бота:",
                    'en': "📢 Subscribe to the following channels to use the bot:"
                }
                await callback.bot.send_message(
                    callback.message.chat.id,
                    texts.get(lang, texts['uz']),
                    reply_markup=get_subscribe_button(channels, lang)
                )
                await UserStates.waiting_for_obuna.set()
                return

        # Request first name
        texts = {
            'uz': "📝 Ism va familiyangizni kiriting (masalan: Aziz Azizov):",
            'ru': "📝 Введите ваше имя и фамилию (например: Aziz Azizov):",
            'en': "📝 Enter your first and last name (e.g., Aziz Azizov):"
        }
        await callback.bot.send_message(
            callback.message.chat.id,
            texts.get(lang, texts['uz'])
        )
        await UserStates.waiting_for_full_name.set()

    except Exception as e:
        print(f"❌ Language selection error: {e}")
        import traceback
        traceback.print_exc()
        await callback.answer("❌ Xatolik!", show_alert=True)


async def change_language_callback(callback: types.CallbackQuery, state: FSMContext):
    """Handle change language callback."""
    try:
        lang = callback.data.split('_')[2]  # 'change_lang_uz', 'change_lang_ru', 'change_lang_en'
        db = Database()
        user_id = callback.from_user.id

        # Save the new language
        success = db.set_user_language(user_id, lang)
        if not success:
            await callback.answer("❌ Xatolik yuz berdi!", show_alert=True)
            return

        # Language names
        lang_names = {
            'uz': "O'zbek tili",
            'ru': "Русский язык",
            'en': "English"
        }
        success_texts = {
            'uz': f"✅ Til o'zgartirildi: {lang_names.get(lang, lang)}",
            'ru': f"✅ Язык изменен: {lang_names.get(lang, lang)}",
            'en': f"✅ Language changed: {lang_names.get(lang, lang)}"
        }

        # ReplyKeyboard bilan yangi xabar yuboramiz
        await callback.message.answer(
            success_texts.get(lang, success_texts['uz']),
            reply_markup=get_main_menu(lang)  # ReplyKeyboardMarkup
        )

        # Eski inline xabarni o‘chiramiz
        await callback.message.delete()

        await callback.answer()
        await state.finish()

    except Exception as e:
        print(f"Change language callback error: {e}")
        import traceback
        traceback.print_exc()
        await callback.answer("❌ Xatolik yuz berdi!", show_alert=True)


async def check_subscription_callback(callback: types.CallbackQuery, state: FSMContext):
    """TUZATILGAN obuna tekshirish callback."""
    try:
        db = Database()
        user_id = callback.from_user.id
        user = db.get_user(user_id)
        lang = user[13] if user and len(user) > 13 else 'uz'

        channels = db.get_all_channels()
        print(f"📋 Obuna tekshirish: {len(channels)} ta kanal")
        print(f"🔍 Kanallar: {channels}")

        subscribed = await check_user_subscription(callback.bot, user_id, channels)
        print(f"📊 Obuna natijasi: {subscribed}")

        if subscribed:
            await callback.message.delete()
            success_texts = {
                'uz': "✅ Obuna tasdiqlandi!",
                'ru': "✅ Подписка подтверждена!",
                'en': "✅ Subscription confirmed!"
            }
            await callback.answer(success_texts.get(lang, success_texts['uz']))

            # Agar user to'liq ro'yxatdan o'tgan bo'lsa - asosiy menyuni ko'rsatish
            if user and user[2] and user[3] and user[2] != '' and user[3] != '':
                welcome_texts = {
                    'uz': f"👋 Xush kelibsiz, {user[2]}!",
                    'ru': f"👋 Добро пожаловать, {user[2]}!",
                    'en': f"👋 Welcome, {user[2]}!"
                }
                status = db.get_user_registration_status(user_id)
                status_msg = get_status_message(status['status'], lang)

                await callback.bot.send_message(
                    callback.message.chat.id,
                    welcome_texts.get(lang, welcome_texts['uz']) + "\n\n" + status_msg,
                    reply_markup=get_main_menu(lang)
                )
                await state.finish()
                return

            # Agar user mavjud lekin ma'lumotlar to'liq emas
            texts = {
                'uz': "📝 Ism va familiyangizni kiriting (masalan: Aziz Azizov):",
                'ru': "📝 Введите ваше имя и фамилию (например: Aziz Azizov):",
                'en': "📝 Enter your first and last name (e.g., Aziz Azizov):"
            }
            await callback.bot.send_message(
                callback.message.chat.id,
                texts.get(lang, texts['uz'])
            )
            await UserStates.waiting_for_full_name.set()

        else:
            error_texts = {
                'uz': "❌ Barcha kanallarga obuna bo'lmagansiz!\nIltimos, avval barcha kanallarga obuna bo'ling.",
                'ru': "❌ Вы не подписаны на все каналы!\nПожалуйста, сначала подпишитесь на все каналы.",
                'en': "❌ You are not subscribed to all channels!\nPlease subscribe to all channels first."
            }
            await callback.answer(error_texts.get(lang, error_texts['uz']), show_alert=True)

    except Exception as e:
        print(f"❌ Check subscription error: {e}")
        import traceback
        traceback.print_exc()
        await callback.answer("❌ Xatolik!", show_alert=True)


async def process_full_name(message: types.Message, state: FSMContext):
    """Process full name input (first name and last name together)."""
    try:
        db = Database()
        user_id = message.from_user.id
        user = db.get_user(user_id)
        lang = user[13] if user and len(user) > 13 else 'uz'

        full_name = message.text.strip()

        # Full name validation
        parts = full_name.split()
        if len(parts) < 2:
            error_texts = {
                'uz': "❌ Iltimos, ism va familiyangizni to‘liq kiriting (masalan: Aziz Azizov):",
                'ru': "❌ Пожалуйста, введите имя и фамилию полностью (например: Aziz Azizov):",
                'en': "❌ Please enter your full name (e.g., Aziz Azizov):"
            }
            await message.answer(error_texts.get(lang, error_texts['uz']))
            return

        first_name, last_name = parts[0], ' '.join(parts[1:])

        # Validate first name
        if len(first_name) < 2:
            error_texts = {
                'uz': "❌ Ism juda qisqa. Kamida 2 ta harf kiriting:",
                'ru': "❌ Имя слишком короткое. Введите минимум 2 буквы:",
                'en': "❌ First name is too short. Enter at least 2 letters:"
            }
            await message.answer(error_texts.get(lang, error_texts['uz']))
            return
        if len(first_name) > 50:
            error_texts = {
                'uz': "❌ Ism juda uzun. Qisqartiring:",
                'ru': "❌ Имя слишком длинное. Сократите:",
                'en': "❌ First name is too long. Shorten it:"
            }
            await message.answer(error_texts.get(lang, error_texts['uz']))
            return

        # Validate last name
        if len(last_name) < 2:
            error_texts = {
                'uz': "❌ Familiya juda qisqa. Kamida 2 ta harf kiriting:",
                'ru': "❌ Фамилия слишком короткая. Введите минимум 2 буквы:",
                'en': "❌ Last name is too short. Enter at least 2 letters:"
            }
            await message.answer(error_texts.get(lang, error_texts['uz']))
            return
        if len(last_name) > 50:
            error_texts = {
                'uz': "❌ Familiya juda uzun. Qisqartiring:",
                'ru': "❌ Фамилия слишком длинная. Сократите:",
                'en': "❌ Last name is too long. Shorten it:"
            }
            await message.answer(error_texts.get(lang, error_texts['uz']))
            return

        # Store full name
        await state.update_data(full_name=full_name)

        # Request phone number
        texts = {
            'uz': "📱 Telefon raqamingizni yuboring:",
            'ru': "📱 Отправьте ваш номер телефона:",
            'en': "📱 Send your phone number:"
        }
        await message.answer(
            texts.get(lang, texts['uz']),
            reply_markup=get_contact_keyboard(lang)
        )
        await UserStates.waiting_for_contact.set()

    except Exception as e:
        print(f"Process full name error: {e}")
        await message.answer("❌ Xatolik yuz berdi!")


async def process_contact(message: types.Message, state: FSMContext):
    """Process contact information."""
    try:
        db = Database()
        user_id = message.from_user.id
        user = db.get_user(user_id)
        lang = user[13] if user and len(user) > 13 else 'uz'

        # Get full name from state
        data = await state.get_data()
        full_name = data.get('full_name', '')

        if message.contact:
            phone = message.contact.phone_number
            if not phone.startswith('+'):
                phone = '+' + phone
        elif message.text:
            phone = message.text.strip()
            import re
            clean_phone = re.sub(r'[^\d\+]', '', phone)
            if not re.match(r'^\+?[0-9]{9,15}$', clean_phone):
                error_texts = {
                    'uz': "❌ Noto'g'ri telefon raqam formati!\nMisol: +998901234567",
                    'ru': "❌ Неверный формат номера телефона!\nПример: +998901234567",
                    'en': "❌ Invalid phone number format!\nExample: +998901234567"
                }
                await message.answer(error_texts.get(lang, error_texts['uz']))
                return
            phone = clean_phone if clean_phone.startswith('+') else '+' + clean_phone
        else:
            error_texts = {
                'uz': "❌ Telefon raqam yuboring yoki 'Kontaktni ulashish' tugmasini bosing!",
                'ru': "❌ Отправьте номер телефона или нажмите кнопку 'Поделиться контактом'!",
                'en': "❌ Send phone number or press 'Share contact' button!"
            }
            await message.answer(error_texts.get(lang, error_texts['uz']))
            return

        # Save user data
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET full_name = ?, phone_number = ? WHERE telegram_id = ?",
                (full_name, phone, user_id)
            )
            conn.commit()

        # If Google Sheets is enabled, save data
        if SHEETS_MODE:
            try:
                save_user_with_qr_to_sheets(user_id, full_name, phone)
            except Exception as e:
                print(f"Google Sheets save error: {e}")

        # Clear state
        await state.finish()

        # Registration success message
        success_texts = {
            'uz': f"✅ Ro'yxatdan muvaffaqiyatli o'tdingiz!\n\n👤 Ism: {full_name}\n📱 Telefon: {phone}",
            'ru': f"✅ Вы успешно зарегистрированы!\n\n👤 Имя: {full_name}\n📱 Телефон: {phone}",
            'en': f"✅ You are successfully registered!\n\n👤 Name: {full_name}\n📱 Phone: {phone}"
        }

        await message.answer(
            success_texts.get(lang, success_texts['uz']),
            reply_markup=get_main_menu(lang),
            parse_mode='HTML'
        )

    except Exception as e:
        print(f"Process contact error: {e}")
        import traceback
        traceback.print_exc()
        await message.answer("❌ Xatolik yuz berdi!")


async def event_list_handler(message: types.Message):
    """Display the latest active event."""
    try:
        db = Database()
        user_id = message.from_user.id
        user = db.get_user(user_id)
        lang = user[13] if user and len(user) > 13 else 'uz'

        # Check if user is registered
        if not user or not user[2] or not user[3] or user[2] == '' or user[3] == '':
            not_reg_texts = {
                'uz': "❌ Avval ro'yxatdan o'tishingiz kerak!\nIltimos /start bosing",
                'ru': "❌ Сначала нужно зарегистрироваться!\nПожалуйста нажмите /start",
                'en': "❌ You need to register first!\nPlease press /start"
            }
            await message.answer(not_reg_texts.get(lang, not_reg_texts['uz']))
            return

        # Get the latest active event
        events = db.get_all_active_events(lang)
        if not events:
            no_events = {
                'uz': "📅 Hozirda faol tadbirlar mavjud emas",
                'ru': "📅 В настоящее время нет активных мероприятий",
                'en': "📅 No active events available at the moment"
            }
            await message.answer(no_events.get(lang, no_events['uz']))
            return

        # Select the latest event (highest id or latest created_at)
        latest_event = max(events, key=lambda x: x[7])  # Assuming created_at is at index 7
        event_id, event_name, event_date, event_time, event_address, payment_amount, _, _ = latest_event

        # Check if user is approved for this event
        status = db.get_user_registration_status(user_id)
        if status['status'] == 'approved' and user[4] == event_id:
            approved_texts = {
                'uz': f"✅ Siz ushbu tadbir uchun allaqachon tasdiqlangansiz: {event_name}",
                'ru': f"✅ Вы уже подтверждены для этого мероприятия: {event_name}",
                'en': f"✅ You are already approved for this event: {event_name}"
            }
            await message.answer(
                approved_texts.get(lang, approved_texts['uz']),
                reply_markup=get_main_menu(lang)
            )
            return

        # Prepare event details
        event_texts = {
            'uz': f"""
🎪 <b>Tadbir:</b> {event_name}
📅 <b>Sana:</b> {event_date}
🕐 <b>Vaqt:</b> {event_time}
📍 <b>Manzil:</b> {event_address}
💰 <b>To'lov miqdori:</b> {payment_amount:,.0f} so'm

Tanlang:
""",
            'ru': f"""
🎪 <b>Мероприятие:</b> {event_name}
📅 <b>Дата:</b> {event_date}
🕐 <b>Время:</b> {event_time}
📍 <b>Адрес:</b> {event_address}
💰 <b>Сумма оплаты:</b> {payment_amount:,.0f} сум

Выберите:
""",
            'en': f"""
🎪 <b>Event:</b> {event_name}
📅 <b>Date:</b> {event_date}
🕐 <b>Time:</b> {event_time}
📍 <b>Address:</b> {event_address}
💰 <b>Payment amount:</b> {payment_amount:,.0f} UZS

Select:
"""
        }

        # Create inline keyboard with Pay and Cancel buttons
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton(
                {'uz': "💳 To'lov qilish", 'ru': "💳 Оплатить", 'en': "💳 Pay"}.get(lang, "💳 To'lov qilish"),
                callback_data=f"pay_event_{event_id}"
            ),
            InlineKeyboardButton(
                {'uz': "❌ Bekor qilish", 'ru': "❌ Отменить", 'en': "❌ Cancel"}.get(lang, "❌ Bekor qilish"),
                callback_data="cancel_payment"
            )
        )

        await message.answer(
            event_texts.get(lang, event_texts['uz']),
            reply_markup=keyboard,
            parse_mode='HTML'
        )

    except Exception as e:
        print(f"Event list error: {e}")
        import traceback
        traceback.print_exc()
        await message.answer("❌ Xatolik yuz berdi!")


async def pay_event_callback(callback: types.CallbackQuery, state: FSMContext):
    """Handle 'Pay' button for the selected event."""
    try:
        event_id = int(callback.data.split('_')[2])  # Handles 'pay_event_'
        db = Database()
        user_id = callback.from_user.id
        user = db.get_user(user_id)
        lang = user[13] if user and len(user) > 13 else 'uz'

        # Check if user is approved for this event
        status = db.get_user_registration_status(user_id)
        if status['status'] == 'approved' and user[4] == event_id:
            approved_texts = {
                'uz': "✅ Siz ushbu tadbir uchun allaqachon tasdiqlangansiz!",
                'ru': "✅ Вы уже подтверждены для этого мероприятия!",
                'en': "✅ You are already approved for this event!"
            }
            await callback.message.edit_text(
                approved_texts.get(lang, approved_texts['uz']),
                reply_markup=get_back_to_main_keyboard(lang),
                parse_mode='HTML'
            )
            await callback.answer()
            return

        # If approved for a different event, reset payment status for new event
        if status['status'] == 'approved' and user[4] != event_id:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET payment_status = 'pending', approved = 0, qr_code = NULL, qr_id = ? WHERE telegram_id = ?",
                    (db._generate_unique_qr_id(), user_id)
                )
                conn.commit()

        event = db.get_event_by_id(event_id, lang)
        if not event:
            await callback.answer("❌ Tadbir topilmadi!", show_alert=True)
            return

        # 📜 Tadbir shartlari
        terms_texts = {
            'uz': """
📜 <b>Tadbir shartlari:</b>
- Tadbir ma'lumotlarini sir saqlash;
- Telefonlarni mas'ul xodimlarga topshirish;
- Ruxsatsiz video yoki rasmga olmaslik;
- Tartib va intizomga rioya qilish;
- Tadbirga o‘z vaqtida yetib kelish;
- To‘lov miqdorini to‘liq amalga oshirish majburiy;
- To‘lovdan keyin qaytarish mumkin emas.

✅ Shartlarga rozimisiz? Rozilik bering:
""",
            'ru': """
📜 <b>Условия мероприятия:</b>
- Соблюдать конфиденциальность информации о мероприятии;
- Передавать телефоны ответственному персоналу;
- Не производить фото- и видеосъемку без разрешения;
- Соблюдать порядок и дисциплину;
- Прибывать на мероприятие вовремя;
- Полная оплата обязательна;
- Возврат средств после оплаты невозможен.

✅ Согласны с условиями? Подтвердите согласие:
""",
            'en': """
📜 <b>Event Terms:</b>
- Keep event information confidential;
- Hand over phones to responsible personnel;
- Do not take photos/videos without permission;
- Maintain order and discipline;
- Arrive at the event on time;
- Full payment is mandatory;
- No refunds after payment.

✅ Agree with the terms? Confirm your consent:
"""
        }

        # Inline keyboard with Agree and Cancel buttons
        terms_keyboard = InlineKeyboardMarkup(row_width=2)
        terms_keyboard.add(
            InlineKeyboardButton(
                {'uz': "✅ Roziman", 'ru': "✅ Согласен", 'en': "✅ Agree"}.get(lang, "✅ Roziman"),
                callback_data=f"confirm_terms_{event_id}"
            ),
            InlineKeyboardButton(
                {'uz': "❌ Bekor qilish", 'ru': "❌ Отменить", 'en': "❌ Cancel"}.get(lang, "❌ Bekor qilish"),
                callback_data="cancel_payment"
            )
        )

        await callback.message.edit_text(
            terms_texts.get(lang, terms_texts['uz']) + f"\n🎪 <b>Tadbir:</b> {event[1]}",
            reply_markup=terms_keyboard,
            parse_mode='HTML'
        )
        await callback.answer()

    except Exception as e:
        print(f"Pay event error: {e}")
        import traceback
        traceback.print_exc()
        await callback.answer("❌ Xatolik!", show_alert=True)


async def cancel_payment_callback(callback: types.CallbackQuery, state: FSMContext):
    """Handle 'Cancel Payment' button."""
    try:
        db = Database()
        user_id = callback.from_user.id
        user = db.get_user(user_id)
        lang = user[13] if user and len(user) > 13 else 'uz'

        # Clear event selection
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET event_id = NULL WHERE telegram_id = ?", (user_id,))
            conn.commit()

        await callback.message.delete()

        cancel_texts = {
            'uz': "❌ To'lov bekor qilindi",
            'ru': "❌ Платеж отменен",
            'en': "❌ Payment cancelled"
        }

        await callback.bot.send_message(
            callback.message.chat.id,
            cancel_texts.get(lang, cancel_texts['uz']),
            reply_markup=get_main_menu(lang),
            parse_mode='HTML'
        )

        await state.finish()
        await callback.answer()

    except Exception as e:
        print(f"Cancel payment error: {e}")
        await callback.answer("❌ Xatolik!", show_alert=True)


async def process_screenshot(message: types.Message, state: FSMContext):
    """Process payment screenshot."""
    try:
        db = Database()
        user_id = message.from_user.id
        user = db.get_user(user_id)
        lang = user[13] if user and len(user) > 13 else 'uz'

        if not message.photo:
            error_texts = {
                'uz': "❌ Iltimos, chekni rasm sifatida yuboring!",
                'ru': "❌ Пожалуйста, отправьте чек как изображение!",
                'en': "❌ Please send receipt as image!"
            }
            await message.answer(error_texts.get(lang, error_texts['uz']))
            return

        file_id = message.photo[-1].file_id

        # Update payment status
        db.update_payment_status(user_id, 'pending_approval')

        # Admin notification
        event = db.get_event_by_id(user[4], lang) if user[4] else None
        event_name = event[1] if event else 'Noma\'lum tadbir'
        admin_message = f"""
💳 <b>YANGI TO'LOV CHEKI</b>

👤 <b>Ism:</b> {user[2]}
📱 <b>Telefon:</b> {user[3]}
🎪 <b>Tadbir:</b> {event_name}
🆔 <b>User ID:</b> <code>{user_id}</code>

✅ Tasdiqlash: /approve_{user_id}
❌ Rad etish: /reject_{user_id}
"""

        # Send to admins
        for admin_id in config.ADMINS:
            try:
                await message.bot.send_photo(
                    admin_id,
                    file_id,
                    caption=admin_message,
                    parse_mode='HTML',
                    reply_markup=get_admin_approval_keyboard(user_id, lang)
                )
            except Exception as e:
                print(f"Admin {admin_id} ga yuborishda xatolik: {e}")

        success_texts = {
            'uz': "✅ Chek muvaffaqiyatli yuborildi!\n⏳ Admin tekshiruvi kutilmoqda...",
            'ru': "✅ Чек успешно отправлен!\n⏳ Ожидается проверка администратора...",
            'en': "✅ Receipt successfully sent!\n⏳ Waiting for admin review..."
        }

        await message.answer(
            success_texts.get(lang, success_texts['uz']),
            reply_markup=get_main_menu(lang),
            parse_mode='HTML'
        )

        await state.finish()

        # Save to Google Sheets if enabled
        if SHEETS_MODE:
            try:
                save_user_with_qr_to_sheets(user_id, user[2], user[3])
            except Exception as e:
                print(f"Google Sheets save error: {e}")

    except Exception as e:
        print(f"Process screenshot error: {e}")
        import traceback
        traceback.print_exc()
        await message.answer("❌ Xatolik yuz berdi!")


async def my_info_handler(message: types.Message):
    """Display user information."""
    try:
        db = Database()
        user_id = message.from_user.id
        user = db.get_user(user_id)

        if not user or not user[2] or not user[3] or user[2] == '' or user[3] == '':
            error_texts = {
                'uz': "❌ Siz hali ro'yxatdan o'tmagansiz!\nIltimos /start bosing",
                'ru': "❌ Вы еще не зарегистрированы!\nПожалуйста нажмите /start",
                'en': "❌ You are not registered yet!\nPlease press /start"
            }
            await message.answer(error_texts.get('uz', error_texts['uz']))
            return

        lang = user[13] if len(user) > 13 and user[13] else 'uz'
        status = db.get_user_registration_status(user_id)

        # Event info
        event = db.get_event_by_id(user[4], lang) if user[4] else None
        event_name = event[1] if event else "-"

        # Status text
        status_text = get_status_message(status['status'], lang)

        # Agar tasdiqlangan bo'lsa — QR kod va to'liq chipta ma'lumotlari
        if status['status'] == 'approved':
            try:
                qr_image = db.get_qr_code_image(user_id)
                if qr_image:
                    ticket_number = user[7] if len(user) > 7 else user_id
                    texts = {
                        'uz': f"""✅ <b>Tabriklaymiz!</b> To'lovingiz tasdiqlandi.
Bu QR sizning elektron chiptangiz.

🎟 <b>Ishtirokchi:</b> {user[2]}
📱 <b>Telefon:</b> {user[3]}
🎪 <b>Tadbir:</b> {event_name}
🆔 <b>Chipta raqami:</b> <code>{ticket_number}</code>

<b>Eslatma!</b>
Boshqa ishtirokchi tomonidan chiptangiz o'zlashtirilmasligi uchun, ushbu chipta ma'lumotlaringizni sir saqlash tavsiya etiladi!!!
""",
                        'ru': f"""✅ <b>Поздравляем!</b> Ваша оплата подтверждена.
Этот QR — ваш электронный билет.

🎟 <b>Участник:</b> {user[2]}
📱 <b>Телефон:</b> {user[3]}
🎪 <b>Мероприятие:</b> {event_name}
🆔 <b>Номер билета:</b> <code>{ticket_number}</code>

<b>Важно!</b>
Чтобы ваш билет не был использован другим участником, храните данные билета в секрете!!!
""",
                        'en': f"""✅ <b>Congratulations!</b> Your payment has been confirmed.
This QR is your e-ticket.

🎟 <b>Participant:</b> {user[2]}
📱 <b>Phone:</b> {user[3]}
🎪 <b>Event:</b> {event_name}
🆔 <b>Ticket number:</b> <code>{ticket_number}</code>

<b>Note!</b>
To prevent your ticket from being misused by others, keep your ticket information confidential!!!
"""
                    }

                    await message.answer_photo(
                        qr_image,
                        caption=texts.get(lang, texts['uz']),
                        parse_mode='HTML'
                    )
                    return  # Approved bo'lsa boshqa ma'lumotlarni chiqarmaymiz
            except Exception as qr_error:
                print(f"QR kod rasmini yuborishda xatolik: {qr_error}")

        # Agar approved bo'lmasa — oddiy profil ma'lumotlari
        info_texts = {
            'uz': f"""
📋 <b>MENING MA'LUMOTLARIM</b>

👤 <b>To'liq ism:</b> {user[2]}
📱 <b>Telefon:</b> {user[3]}
🎪 <b>Tanlangan tadbir:</b> {event_name}
📊 <b>Holat:</b> {status_text}
🆔 <b>ID:</b> <code>{user[7] if len(user) > 7 else user_id}</code>
🌐 <b>Til:</b> {lang.upper()}
""",
            'ru': f"""
📋 <b>МОИ ДАННЫЕ</b>

👤 <b>Полное имя:</b> {user[2]}
📱 <b>Телефон:</b> {user[3]}
🎪 <b>Выбранное мероприятие:</b> {event_name}
📊 <b>Статус:</b> {status_text}
🆔 <b>ID:</b> <code>{user[7] if len(user) > 7 else user_id}</code>
🌐 <b>Язык:</b> {lang.upper()}
""",
            'en': f"""
📋 <b>MY INFORMATION</b>

👤 <b>Full name:</b> {user[2]}
📱 <b>Phone:</b> {user[3]}
🎪 <b>Selected event:</b> {event_name}
📊 <b>Status:</b> {status_text}
🆔 <b>ID:</b> <code>{user[7] if len(user) > 7 else user_id}</code>
🌐 <b>Language:</b> {lang.upper()}
"""
        }

        await message.answer(
            info_texts.get(lang, info_texts['uz']),
            reply_markup=get_user_info_keyboard(user_id, lang),
            parse_mode='HTML'
        )

    except Exception as e:
        print(f"My info error: {e}")
        import traceback
        traceback.print_exc()
        await message.answer("❌ Ma'lumotlarni olishda xatolik!")



async def contact_handler(message: types.Message):
    """Handle contact request."""
    try:
        db = Database()
        user_id = message.from_user.id
        user = db.get_user(user_id)
        lang = user[13] if user and len(user) > 13 and user[13] else 'uz'

        admin_username = getattr(config, 'ADMIN_USERNAME', '@husniyamee')

        contact_texts = {
            'uz': f"📞 Aloqa uchun: {admin_username}\n\n💬 Savollaringiz bo'lsa, yuqoridagi admin bilan bog'laning.",
            'ru': f"📞 Для связи: {admin_username}\n\n💬 Если у вас есть вопросы, свяжитесь с администратором выше.",
            'en': f"📞 For contact: {admin_username}\n\n💬 If you have questions, contact the admin above."
        }

        await message.answer(
            contact_texts.get(lang, contact_texts['uz']),
            reply_markup=get_main_menu(lang),
            parse_mode='HTML'
        )

    except Exception as e:
        print(f"Contact error: {e}")
        await message.answer("❌ Xatolik yuz berdi!")


async def change_language_handler(message: types.Message):
    """Handle change language request."""
    try:
        db = Database()
        user_id = message.from_user.id
        user = db.get_user(user_id)
        lang = user[13] if user and len(user) > 13 else 'uz'

        await message.answer(
            {
                'uz': "🌐 Yangi tilni tanlang:",
                'ru': "🌐 Выберите новый язык:",
                'en': "🌐 Select new language:"
            }.get(lang, "🌐 Yangi tilni tanlang:"),
            reply_markup=get_change_language_keyboard()
        )

    except Exception as e:
        print(f"Change language error: {e}")
        await message.answer("❌ Xatolik yuz berdi!")



async def back_to_main_callback(callback: types.CallbackQuery, state: FSMContext):
    """Handle back to main menu callback."""
    try:
        db = Database()
        user_id = callback.from_user.id
        user = db.get_user(user_id)
        lang = user[13] if user and len(user) > 13 else 'uz'

        await callback.message.delete()

        welcome_texts = {
            'uz': f"👋 Assalomu alaykum, {user[2]}!",
            'ru': f"👋 Здравствуйте, {user[2]}!",
            'en': f"👋 Hello, {user[2]}!"
        }

        status = db.get_user_registration_status(user_id)
        status_msg = get_status_message(status['status'], lang)

        await callback.bot.send_message(
            callback.message.chat.id,
            welcome_texts.get(lang, welcome_texts['uz']) + "\n\n" + status_msg,
            reply_markup=get_main_menu(lang),
            parse_mode='HTML'
        )

        await state.finish()
        await callback.answer()

    except Exception as e:
        print(f"Back to main error: {e}")
        await callback.answer("❌ Xatolik!", show_alert=True)


async def my_qr_callback(callback: types.CallbackQuery, state: FSMContext):
    """Handle 'View my QR code' callback."""
    try:
        db = Database()
        user_id = callback.from_user.id
        user = db.get_user(user_id)
        lang = user[13] if user and len(user) > 13 else 'uz'

        status = db.get_user_registration_status(user_id)
        if status['status'] != 'approved':
            error_texts = {
                'uz': "❌ QR kod faqat tasdiqlangan to'lovdan so'ng mavjud!",
                'ru': "❌ QR код доступен только после подтверждения платежа!",
                'en': "❌ QR code is available only after payment approval!"
            }
            await callback.answer(error_texts.get(lang, error_texts['uz']), show_alert=True)
            return

        qr_image = db.get_qr_code_image(user_id)
        if not qr_image:
            error_texts = {
                'uz': "❌ QR kod topilmadi!",
                'ru': "❌ QR код не найден!",
                'en': "❌ QR code not found!"
            }
            await callback.answer(error_texts.get(lang, error_texts['uz']), show_alert=True)
            return

        qr_texts = {
            'uz': f"🎫 Sizning QR kodingiz\n🆔 <b>ID:</b> <code>{user[7] if len(user) > 7 else user_id}</code>",
            'ru': f"🎫 Ваш QR код\n🆔 <b>ID:</b> <code>{user[7] if len(user) > 7 else user_id}</code>",
            'en': f"🎫 Your QR code\n🆔 <b>ID:</b> <code>{user[7] if len(user) > 7 else user_id}</code>"
        }

        await callback.message.delete()
        await callback.bot.send_photo(
            callback.message.chat.id,
            qr_image,
            caption=qr_texts.get(lang, qr_texts['uz']),
            reply_markup=get_user_info_keyboard(user_id, lang),
            parse_mode='HTML'
        )
        await callback.answer()

    except Exception as e:
        print(f"My QR error: {e}")
        await callback.answer("❌ Xatolik!", show_alert=True)


async def payment_status_callback(callback: types.CallbackQuery, state: FSMContext):
    """Handle 'Payment status' callback."""
    try:
        db = Database()
        user_id = callback.from_user.id
        user = db.get_user(user_id)
        lang = user[13] if user and len(user) > 13 else 'uz'

        status = db.get_user_registration_status(user_id)
        status_text = get_status_message(status['status'], lang)

        event = db.get_event_by_id(user[4], lang) if user[4] else None
        event_name = event[1] if event else "-"

        status_texts = {
            'uz': f"💳 To'lov holati: {status_text}\n🎪 Tadbir: {event_name}",
            'ru': f"💳 Статус платежа: {status_text}\n🎪 Мероприятие: {event_name}",
            'en': f"💳 Payment status: {status_text}\n🎪 Event: {event_name}"
        }

        await callback.message.edit_text(
            status_texts.get(lang, status_texts['uz']),
            reply_markup=get_user_info_keyboard(user_id, lang),
            parse_mode='HTML'
        )
        await callback.answer()

    except Exception as e:
        print(f"Payment status error: {e}")
        await callback.answer("❌ Xatolik!", show_alert=True)


async def confirm_terms_callback(callback: types.CallbackQuery, state):
    """TUZATILGAN shartlarga rozilik callback"""
    try:
        event_id = int(callback.data.split('_')[2])
        user_id = callback.from_user.id

        db = Database()  # db ni to'g'ri import qilish
        user = db.get_user(user_id)
        lang = user[13] if user and len(user) > 13 else 'uz'

        # Event ID ni yangilash
        db.update_user_event(user_id, event_id)

        event = db.get_event_by_id(event_id, lang)
        event_name = event[1]

        # Config dan karta ma'lumotlarini olish
        card_number = getattr(config, 'CARD_NUMBER', "8600 0000 0000 0000")
        card_owner = getattr(config, 'CARD_OWNER', "Ism Familiya")

        texts = {
            'uz': f"""
🎪 <b>Tadbir:</b> {event_name}
📅 <b>Sana:</b> {event[2]}
🕐 <b>Vaqt:</b> {event[3]}
📍 <b>Manzil:</b> {event[4]}
💰 <b>To'lov miqdori:</b> {event[5]:,.0f} so'm

💳 <b>Karta raqami:</b> <code>{card_number}</code>
👤 <b>Karta egasi:</b> {card_owner}

📸 To'lovdan so'ng chek rasmini yuboring:
""",
            'ru': f"""
🎪 <b>Мероприятие:</b> {event_name}
📅 <b>Дата:</b> {event[2]}
🕐 <b>Время:</b> {event[3]}
📍 <b>Адрес:</b> {event[4]}
💰 <b>Сумма оплаты:</b> {event[5]:,.0f} сум

💳 <b>Номер карты:</b> <code>{card_number}</code>
👤 <b>Владелец карты:</b> {card_owner}

📸 После оплаты отправьте чек:
""",
            'en': f"""
🎪 <b>Event:</b> {event_name}
📅 <b>Date:</b> {event[2]}
🕐 <b>Time:</b> {event[3]}
📍 <b>Address:</b> {event[4]}
💰 <b>Payment amount:</b> {event[5]:,.0f} UZS

💳 <b>Card number:</b> <code>{card_number}</code>
👤 <b>Card owner:</b> {card_owner}

📸 After payment, send receipt:
"""
        }

        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton(
                {'uz': "❌ Bekor qilish", 'ru': "❌ Отменить", 'en': "❌ Cancel"}.get(lang, "❌ Bekor qilish"),
                callback_data="cancel_payment"
            )
        )

        await callback.message.edit_text(
            texts.get(lang, texts['uz']),
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        await UserStates.waiting_for_payment_screenshot.set()
        await callback.answer()

    except Exception as e:
        print(f"❌ Confirm terms error: {e}")
        import traceback
        traceback.print_exc()
        await callback.answer("❌ Xatolik!", show_alert=True)



def register_user_handlers(dp: Dispatcher):
    """Register user handlers."""
    dp.register_message_handler(start_handler, commands=['start'], state='*')
    dp.register_message_handler(event_list_handler, text=['🎪 Tadbirlar', '🎪 Мероприятия', '🎪 Events'])
    dp.register_message_handler(my_info_handler, text=['ℹ️ Mening ma\'lumotlarim', 'ℹ️ Мои данные', 'ℹ️ My info'])
    dp.register_message_handler(contact_handler, text=['📞 Aloqa', '📞 Контакт', '📞 Contact'])
    dp.register_message_handler(change_language_handler,
                                text=['🌐 Tilni o\'zgartirish', '🌐 Сменить язык', '🌐 Change language'])

    dp.register_message_handler(process_full_name, state=UserStates.waiting_for_full_name, content_types=['text'])
    dp.register_message_handler(process_contact, state=UserStates.waiting_for_contact,
                                content_types=['text', 'contact'])
    dp.register_message_handler(process_screenshot, state=UserStates.waiting_for_payment_screenshot,
                                content_types=['photo'])


    dp.register_callback_query_handler(select_language_callback, lambda c: c.data.startswith('lang_'), state='*')
    dp.register_callback_query_handler(change_language_callback, lambda c: c.data.startswith('change_lang_'), state='*')
    dp.register_callback_query_handler(check_subscription_callback, lambda c: c.data == 'check_subscription', state='*')
    dp.register_callback_query_handler(pay_event_callback, lambda c: c.data.startswith('pay_event_'), state='*')
    dp.register_callback_query_handler(confirm_terms_callback, lambda c: c.data.startswith('confirm_terms_'), state='*')
    dp.register_callback_query_handler(cancel_payment_callback, lambda c: c.data == 'cancel_payment', state='*')
    dp.register_callback_query_handler(back_to_main_callback, lambda c: c.data == 'back_to_main', state='*')
    dp.register_callback_query_handler(my_qr_callback, lambda c: c.data.startswith('my_qr_'), state='*')
    dp.register_callback_query_handler(payment_status_callback, lambda c: c.data.startswith('payment_status_'),
                                       state='*')

    print("✅ User handlerlari ro'yxatga olindi!")
