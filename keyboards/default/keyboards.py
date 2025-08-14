# ================ KEYBOARDS.PY - TO'G'IRLANGAN VERSIYA ================

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu(lang='uz'):
    """Asosiy menyu"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    buttons = {
        'uz': [
            "🎪 Tadbirlar",
            "ℹ️ Mening ma'lumotlarim",
            "📞 Aloqa",
            "🌐 Tilni o'zgartirish"
        ],
        'ru': [
            "🎪 Мероприятия",
            "ℹ️ Мои данные",
            "📞 Контакт",
            "🌐 Сменить язык"
        ],
        'en': [
            "🎪 Events",
            "ℹ️ My info",
            "📞 Contact",
            "🌐 Change language"
        ]
    }

    menu_buttons = buttons.get(lang, buttons['uz'])

    keyboard.row(
        KeyboardButton(menu_buttons[0]),
        KeyboardButton(menu_buttons[1])
    )
    keyboard.row(
        KeyboardButton(menu_buttons[2]),
        KeyboardButton(menu_buttons[3])
    )

    return keyboard


def get_language_keyboard():
    """Til tanlash klaviaturasi (start da)"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🇺🇿 O'zbek tili", callback_data="lang_uz"),
        InlineKeyboardButton("🇷🇺 Русский язык", callback_data="lang_ru"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
    )
    return keyboard


def get_change_language_keyboard():
    """Tilni o'zgartirish klaviaturasi (menyudan)"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🇺🇿 O'zbek tili", callback_data="change_lang_uz"),
        InlineKeyboardButton("🇷🇺 Русский язык", callback_data="change_lang_ru"),
        InlineKeyboardButton("🇬🇧 English", callback_data="change_lang_en")
    )
    return keyboard


def get_subscribe_button(channels, lang='uz'):
    """TUZATILGAN: Kanallarga obuna bo'lish tugmalari"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for channel_data in channels:
        try:
            # Database dan keladigan ma'lumotlar: (channel_id, channel_name, channel_username, channel_type)
            print(f"🔍 Processing channel: {channel_data}")

            if len(channel_data) >= 4:
                channel_id, channel_name, channel_username, channel_type = channel_data[:4]
            elif len(channel_data) == 3:
                channel_id, channel_name, channel_username = channel_data
                channel_type = 'public'
            elif len(channel_data) == 2:
                channel_id, channel_name = channel_data
                channel_username = None
                channel_type = 'public'
            else:
                print(f"❌ Invalid channel data format: {channel_data}")
                continue

            print(f"📋 Parsed: ID={channel_id}, Name={channel_name}, Username={channel_username}, Type={channel_type}")

            # URL yaratish - TUZATILGAN mantiq
            url = None

            # 1. Agar channel_username mavjud bo'lsa va to'g'ri bo'lsa
            if channel_username and isinstance(channel_username, str) and channel_username.strip():
                username_clean = channel_username.strip()

                # @ belgisini olib tashlash
                if username_clean.startswith('@'):
                    username_clean = username_clean[1:]

                # Username ni validatsiya qilish
                if username_clean and len(username_clean) > 0 and username_clean != 'none' and username_clean != 'yoq':
                    url = f"https://t.me/{username_clean}"
                    print(f"✅ URL from username: {url}")

            # 2. Agar username yo'q bo'lsa, channel_id dan foydalanish
            if not url:
                if str(channel_id).startswith('@'):
                    # @username formatdagi channel_id
                    username_from_id = str(channel_id)[1:]  # @ ni olib tashlash
                    if username_from_id and username_from_id != 'none':
                        url = f"https://t.me/{username_from_id}"
                        print(f"✅ URL from channel_id (username): {url}")

                elif str(channel_id).startswith('-100'):
                    # Private channel ID
                    channel_numeric_id = str(channel_id)[4:]  # -100 ni olib tashlash
                    url = f"https://t.me/c/{channel_numeric_id}/1"
                    print(f"✅ URL from channel_id (private): {url}")

                elif str(channel_id).isdigit() or (str(channel_id).startswith('-') and str(channel_id)[1:].isdigit()):
                    # Oddiy raqamli ID
                    url = f"https://t.me/c/{str(channel_id).replace('-', '')}/1"
                    print(f"✅ URL from channel_id (numeric): {url}")

            # 3. Fallback: channel_name dan foydalanish (agar boshqa hech narsa ishlamasa)
            if not url:
                # Channel name ni tozalash
                clean_name = str(channel_name).replace('@', '').replace('https://t.me/', '').strip()
                if clean_name and clean_name != 'none' and len(clean_name) > 0:
                    url = f"https://t.me/{clean_name}"
                    print(f"⚠️ Fallback URL from name: {url}")
                else:
                    print(f"❌ Cannot create URL for channel: {channel_data}")
                    continue

            # Display name ni aniqlash
            display_name = channel_name
            if not display_name or display_name == 'none':
                if channel_username:
                    display_name = f"@{channel_username.replace('@', '')}"
                else:
                    display_name = f"Channel {str(channel_id)[:10]}"

            print(f"🎯 Final: Name='{display_name}', URL='{url}'")

            # Tugma qo'shish
            keyboard.add(
                InlineKeyboardButton(f"📢 {display_name}", url=url)
            )

        except Exception as e:
            print(f"❌ Error processing channel {channel_data}: {e}")
            continue

    # "Obunani tekshirish" tugmasi
    check_texts = {
        'uz': "✅ Obunani tekshirish",
        'ru': "✅ Проверить подписку",
        'en': "✅ Check subscription"
    }

    keyboard.add(
        InlineKeyboardButton(
            check_texts.get(lang, check_texts['uz']),
            callback_data="check_subscription"
        )
    )

    return keyboard


def get_contact_keyboard(lang='uz'):
    """Kontakt yuborish klaviaturasi"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=1)

    texts = {
        'uz': "📱 Telefon raqamni yuborish",
        'ru': "📱 Отправить номер телефона",
        'en': "📱 Send phone number"
    }

    keyboard.add(
        KeyboardButton(
            texts.get(lang, texts['uz']),
            request_contact=True
        )
    )

    return keyboard


def get_event_selection_menu(events, lang='uz'):
    """Tadbirlar tanlash menyusi - to'g'irlangan"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for event in events:
        event_id = event[0]
        event_name = event[1]
        event_date = event[2]
        event_price = event[5] if len(event) > 5 else 0

        # Qisqaroq button text
        button_text = f"🎪 {event_name[:25]}... | {event_price:,.0f} so'm"
        if len(event_name) <= 25:
            button_text = f"🎪 {event_name} | {event_price:,.0f} so'm"

        keyboard.add(
            InlineKeyboardButton(
                button_text,
                callback_data=f"select_event_{event_id}"
            )
        )

    # Orqaga tugmasi
    back_texts = {
        'uz': "⬅️ Orqaga",
        'ru': "⬅️ Назад",
        'en': "⬅️ Back"
    }

    keyboard.add(
        InlineKeyboardButton(
            back_texts.get(lang, back_texts['uz']),
            callback_data="back_to_main"
        )
    )

    return keyboard


def get_payment_confirmation_keyboard(lang='uz'):
    """To'lov tasdiqlash klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    done_texts = {
        'uz': "✅ To'lov qildim",
        'ru': "✅ Я оплатил",
        'en': "✅ I paid"
    }

    cancel_texts = {
        'uz': "❌ Bekor qilish",
        'ru': "❌ Отменить",
        'en': "❌ Cancel"
    }

    keyboard.add(
        InlineKeyboardButton(
            done_texts.get(lang, done_texts['uz']),
            callback_data="payment_done"
        ),
        InlineKeyboardButton(
            cancel_texts.get(lang, cancel_texts['uz']),
            callback_data="cancel_payment"
        )
    )

    return keyboard


# ================ ADMIN KLAVIATURALARI ================

def get_admin_keyboard():
    """Admin klaviaturasi"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    keyboard.row(
        KeyboardButton("📊 Statistika"),
        KeyboardButton("✅ Kutilayotgan to'lovlar")
    )
    keyboard.row(
        KeyboardButton("🎪 Marosimlar boshqaruvi"),
        KeyboardButton("📢 Kanallar boshqaruvi")
    )
    # keyboard.row(
    #     KeyboardButton("📋 Google Sheets"),
    #     KeyboardButton("📱 QR Skaner")
    # )
    keyboard.row(
        KeyboardButton("📣 Reklama"),
        # KeyboardButton("👤 User rejimi")
    )

    return keyboard


def get_admin_events_keyboard():
    """Admin uchun tadbirlar menyusi"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton("🎪 Yangi tadbir", callback_data="add_event"),
        InlineKeyboardButton("📋 Tadbirlar ro'yxati", callback_data="list_events")
    )
    keyboard.add(
        InlineKeyboardButton("📊 Tadbir statistikasi", callback_data="events_stats"),
        InlineKeyboardButton("🔄 Tadbirni boshqarish", callback_data="manage_events")
    )
    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_admin")
    )

    return keyboard


def get_admin_channel_menu():
    """Admin kanal menyusi"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton("➕ Kanal qo'shish", callback_data="admin_add_channel"),
        InlineKeyboardButton("📋 Kanallar ro'yxati", callback_data="admin_list_channels")
    )
    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_admin")
    )

    return keyboard


def get_cancel_keyboard(lang='uz'):
    """Bekor qilish klaviaturasi"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)

    cancel_texts = {
        'uz': "❌ Bekor qilish",
        'ru': "❌ Отменить",
        'en': "❌ Cancel"
    }

    keyboard.add(KeyboardButton(cancel_texts.get(lang, cancel_texts['uz'])))
    return keyboard


def get_confirmation_keyboard(lang='uz'):
    """Ha/Yo'q klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    yes_texts = {
        'uz': "✅ Ha",
        'ru': "✅ Да",
        'en': "✅ Yes"
    }

    no_texts = {
        'uz': "❌ Yo'q",
        'ru': "❌ Нет",
        'en': "❌ No"
    }

    keyboard.add(
        InlineKeyboardButton(yes_texts.get(lang, yes_texts['uz']), callback_data="confirm_yes"),
        InlineKeyboardButton(no_texts.get(lang, no_texts['uz']), callback_data="confirm_no")
    )
    return keyboard


def get_events_list_keyboard(events, lang='uz'):
    """Tadbirlar ro'yxati klaviaturasi (admin uchun)"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for event in events:
        event_id = event['id']
        event_name = event['name'][:30] + "..." if len(event['name']) > 30 else event['name']
        event_date = event['date']
        stats = event['stats']
        status = "🟢" if event['is_active'] else "🔴"

        btn_text = f"{status} {event_name} ({stats['approved']} kishi)"

        keyboard.add(
            InlineKeyboardButton(
                btn_text,
                callback_data=f"event_detail_{event_id}"
            )
        )

    # Orqaga tugmasi
    back_texts = {
        'uz': "⬅️ Orqaga",
        'ru': "⬅️ Назад",
        'en': "⬅️ Back"
    }

    keyboard.add(
        InlineKeyboardButton(back_texts.get(lang, back_texts['uz']), callback_data="back_to_admin")
    )

    return keyboard


def get_event_detail_keyboard(event_id, lang='uz'):
    """Tadbir detallari klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    texts = {
        'uz': {
            'stats': '📊 Statistika',
            'users': '👥 Foydalanuvchilar',
            'edit': '✏️ Tahrirlash',
            'toggle': '🔄 Faol/Nofaol',
            'back': '⬅️ Orqaga'
        },
        'ru': {
            'stats': '📊 Статистика',
            'users': '👥 Пользователи',
            'edit': '✏️ Редактировать',
            'toggle': '🔄 Вкл/Выкл',
            'back': '⬅️ Назад'
        },
        'en': {
            'stats': '📊 Statistics',
            'users': '👥 Users',
            'edit': '✏️ Edit',
            'toggle': '🔄 On/Off',
            'back': '⬅️ Back'
        }
    }

    t = texts.get(lang, texts['uz'])

    keyboard.add(
        InlineKeyboardButton(t['stats'], callback_data=f"event_stats_{event_id}"),
        InlineKeyboardButton(t['users'], callback_data=f"event_users_{event_id}")
    )
    keyboard.add(
        InlineKeyboardButton(t['edit'], callback_data=f"edit_event_{event_id}"),
        InlineKeyboardButton(t['toggle'], callback_data=f"toggle_event_{event_id}")
    )
    keyboard.add(
        InlineKeyboardButton(t['back'], callback_data="list_events")
    )

    return keyboard


def get_channels_management_keyboard(lang='uz'):
    """Kanallar boshqaruvi klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    texts = {
        'uz': {
            'add': '➕ Kanal qo\'shish',
            'list': '📋 Kanallar ro\'yxati',
            'back': '⬅️ Orqaga'
        },
        'ru': {
            'add': '➕ Добавить канал',
            'list': '📋 Список каналов',
            'back': '⬅️ Назад'
        },
        'en': {
            'add': '➕ Add channel',
            'list': '📋 Channels list',
            'back': '⬅️ Back'
        }
    }

    t = texts.get(lang, texts['uz'])

    keyboard.add(
        InlineKeyboardButton(t['add'], callback_data="add_channel"),
        InlineKeyboardButton(t['list'], callback_data="list_channels")
    )
    keyboard.add(
        InlineKeyboardButton(t['back'], callback_data="back_to_admin")
    )

    return keyboard


def get_channels_list_keyboard(channels, lang='uz'):
    """Kanallar ro'yxati klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for channel_data in channels:
        if len(channel_data) >= 2:
            channel_id = channel_data[1] if len(channel_data) > 2 else channel_data[0]
            channel_name = channel_data[2] if len(channel_data) > 2 else channel_data[1]
        else:
            channel_id, channel_name = channel_data[0], channel_data[1]

        keyboard.add(
            InlineKeyboardButton(
                f"📢 {channel_name}",
                callback_data=f"channel_detail_{channel_id}"
            )
        )

    back_texts = {
        'uz': "⬅️ Orqaga",
        'ru': "⬅️ Назад",
        'en': "⬅️ Back"
    }

    keyboard.add(
        InlineKeyboardButton(back_texts.get(lang, back_texts['uz']), callback_data="channels_management")
    )

    return keyboard


def get_channel_detail_keyboard(channel_id, lang='uz'):
    """Kanal detallari klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    texts = {
        'uz': {
            'delete': '🗑 O\'chirish',
            'test': '🔍 Tekshirish',
            'back': '⬅️ Orqaga'
        },
        'ru': {
            'delete': '🗑 Удалить',
            'test': '🔍 Проверить',
            'back': '⬅️ Назад'
        },
        'en': {
            'delete': '🗑 Delete',
            'test': '🔍 Test',
            'back': '⬅️ Back'
        }
    }

    t = texts.get(lang, texts['uz'])

    keyboard.add(
        InlineKeyboardButton(t['delete'], callback_data=f"delete_channel_{channel_id}"),
        InlineKeyboardButton(t['test'], callback_data=f"test_channel_{channel_id}")
    )
    keyboard.add(
        InlineKeyboardButton(t['back'], callback_data="list_channels")
    )

    return keyboard


def get_qr_scanner_keyboard(lang='uz'):
    """QR skaner klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    texts = {
        'uz': {
            'scan': '📱 QR kod skanerlash',
            'manual': '✏️ QR ID kiritish',
            'stats': '📊 Kelganlik statistikasi',
            'back': '⬅️ Orqaga'
        },
        'ru': {
            'scan': '📱 Сканировать QR код',
            'manual': '✏️ Ввести QR ID',
            'stats': '📊 Статистика посещений',
            'back': '⬅️ Назад'
        },
        'en': {
            'scan': '📱 Scan QR code',
            'manual': '✏️ Enter QR ID',
            'stats': '📊 Attendance statistics',
            'back': '⬅️ Back'
        }
    }

    t = texts.get(lang, texts['uz'])

    keyboard.add(
        InlineKeyboardButton(t['scan'], callback_data="scan_qr"),
        InlineKeyboardButton(t['manual'], callback_data="manual_qr"),
        InlineKeyboardButton(t['stats'], callback_data="attendance_stats")
    )
    keyboard.add(
        InlineKeyboardButton(t['back'], callback_data="back_to_admin")
    )

    return keyboard


def get_google_sheets_keyboard(lang='uz'):
    """Google Sheets klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    texts = {
        'uz': {
            'export': '📤 Export qilish',
            'sync': '🔄 Sinxronlash',
            'config': '⚙️ Sozlamalar',
            'status': '📊 Holat',
            'back': '⬅️ Orqaga'
        },
        'ru': {
            'export': '📤 Экспорт',
            'sync': '🔄 Синхронизация',
            'config': '⚙️ Настройки',
            'status': '📊 Статус',
            'back': '⬅️ Назад'
        },
        'en': {
            'export': '📤 Export',
            'sync': '🔄 Sync',
            'config': '⚙️ Settings',
            'status': '📊 Status',
            'back': '⬅️ Back'
        }
    }

    t = texts.get(lang, texts['uz'])

    keyboard.add(
        InlineKeyboardButton(t['export'], callback_data="export_sheets"),
        InlineKeyboardButton(t['sync'], callback_data="sync_sheets")
    )
    keyboard.add(
        InlineKeyboardButton(t['config'], callback_data="sheets_config"),
        InlineKeyboardButton(t['status'], callback_data="sheets_status")
    )
    keyboard.add(
        InlineKeyboardButton(t['back'], callback_data="back_to_admin")
    )

    return keyboard


def get_statistics_keyboard(lang='uz'):
    """Statistika klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    texts = {
        'uz': {
            'general': '📈 Umumiy',
            'events': '🎪 Tadbirlar',
            'users': '👥 Foydalanuvchilar',
            'payments': '💳 To\'lovlar',
            'report': '📋 Hisobot',
            'back': '⬅️ Orqaga'
        },
        'ru': {
            'general': '📈 Общая',
            'events': '🎪 Мероприятия',
            'users': '👥 Пользователи',
            'payments': '💳 Платежи',
            'report': '📋 Отчет',
            'back': '⬅️ Назад'
        },
        'en': {
            'general': '📈 General',
            'events': '🎪 Events',
            'users': '👥 Users',
            'payments': '💳 Payments',
            'report': '📋 Report',
            'back': '⬅️ Back'
        }
    }

    t = texts.get(lang, texts['uz'])

    keyboard.add(
        InlineKeyboardButton(t['general'], callback_data="stats_general"),
        InlineKeyboardButton(t['events'], callback_data="stats_events")
    )
    keyboard.add(
        InlineKeyboardButton(t['users'], callback_data="stats_users"),
        InlineKeyboardButton(t['payments'], callback_data="stats_payments")
    )
    keyboard.add(
        InlineKeyboardButton(t['report'], callback_data="export_stats")
    )
    keyboard.add(
        InlineKeyboardButton(t['back'], callback_data="back_to_admin")
    )

    return keyboard


def get_pending_payments_keyboard(pending_users, lang='uz'):
    """Kutilayotgan to'lovlar klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for user in pending_users[:10]:  # Faqat birinchi 10 ta
        user_id = user[1]  # telegram_id
        full_name = user[2]  # full_name
        event_name = user[-1] if user[-1] else "Noma'lum"  # event_name

        btn_text = f"👤 {full_name[:20]}... - {event_name[:15]}..."
        if len(full_name) <= 20:
            btn_text = f"👤 {full_name} - {event_name[:20]}..."

        keyboard.add(
            InlineKeyboardButton(
                btn_text,
                callback_data=f"review_payment_{user_id}"
            )
        )

    # Agar 10 dan ko'p bo'lsa
    if len(pending_users) > 10:
        more_texts = {
            'uz': f"... va yana {len(pending_users) - 10} ta",
            'ru': f"... и еще {len(pending_users) - 10}",
            'en': f"... and {len(pending_users) - 10} more"
        }
        keyboard.add(
            InlineKeyboardButton(
                more_texts.get(lang, more_texts['uz']),
                callback_data="more_pending_payments"
            )
        )

    back_texts = {
        'uz': "⬅️ Orqaga",
        'ru': "⬅️ Назад",
        'en': "⬅️ Back"
    }

    keyboard.add(
        InlineKeyboardButton(back_texts.get(lang, back_texts['uz']), callback_data="back_to_admin")
    )

    return keyboard


def get_user_review_keyboard(user_id, lang='uz'):
    """Foydalanuvchini ko'rib chiqish klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    texts = {
        'uz': {
            'approve': '✅ Tasdiqlash',
            'reject': '❌ Rad etish',
            'details': '📋 Batafsil',
            'back': '⬅️ Orqaga'
        },
        'ru': {
            'approve': '✅ Одобрить',
            'reject': '❌ Отклонить',
            'details': '📋 Подробно',
            'back': '⬅️ Назад'
        },
        'en': {
            'approve': '✅ Approve',
            'reject': '❌ Reject',
            'details': '📋 Details',
            'back': '⬅️ Back'
        }
    }

    t = texts.get(lang, texts['uz'])

    keyboard.add(
        InlineKeyboardButton(t['approve'], callback_data=f"approve_{user_id}"),
        InlineKeyboardButton(t['reject'], callback_data=f"reject_{user_id}")
    )
    keyboard.add(
        InlineKeyboardButton(t['details'], callback_data=f"user_details_{user_id}")
    )
    keyboard.add(
        InlineKeyboardButton(t['back'], callback_data="pending_payments")
    )

    return keyboard


def get_admin_approval_keyboard(user_id, lang='uz'):
    """Admin tasdiqlash klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    texts = {
        'uz': {
            'approve': '✅ Tasdiqlash',
            'reject': '❌ Rad etish'
        },
        'ru': {
            'approve': '✅ Одобрить',
            'reject': '❌ Отклонить'
        },
        'en': {
            'approve': '✅ Approve',
            'reject': '❌ Reject'
        }
    }

    t = texts.get(lang, texts['uz'])

    keyboard.add(
        InlineKeyboardButton(t['approve'], callback_data=f"approve_{user_id}"),
        InlineKeyboardButton(t['reject'], callback_data=f"reject_{user_id}")
    )

    return keyboard


def get_back_to_main_keyboard(lang='uz'):
    """Asosiy menyuga qaytish klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    back_texts = {
        'uz': "⬅️ Asosiy menyuga qaytish",
        'ru': "⬅️ Вернуться в главное меню",
        'en': "⬅️ Back to main menu"
    }

    keyboard.add(
        InlineKeyboardButton(
            back_texts.get(lang, back_texts['uz']),
            callback_data="back_to_main"
        )
    )

    return keyboard


def get_user_info_keyboard(user_id, lang='uz'):
    """User ma'lumotlari klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    texts = {
        'uz': {
            'qr': "🎫 QR kodimni ko'rish",
            'payment': "💳 To'lov holati"
        },
        'ru': {
            'qr': "🎫 Посмотреть мой QR код",
            'payment': "💳 Статус платежа"
        },
        'en': {
            'qr': "🎫 View my QR code",
            'payment': "💳 Payment status"
        }
    }

    t = texts.get(lang, texts['uz'])

    keyboard.add(
        InlineKeyboardButton(
            t['qr'],
            callback_data=f"my_qr_{user_id}"
        ),
        InlineKeyboardButton(
            t['payment'],
            callback_data=f"payment_status_{user_id}"
        )
    )

    return keyboard


# ================ UTILITY FUNCTIONS ================

def create_inline_keyboard(buttons_data, row_width=1):
    """Universal inline keyboard yaratish funksiyasi"""
    keyboard = InlineKeyboardMarkup(row_width=row_width)

    for button_info in buttons_data:
        if len(button_info) == 3 and button_info[2] == 'url':
            # URL tugma
            btn = InlineKeyboardButton(text=button_info[0], url=button_info[1])
        else:
            # Callback tugma
            btn = InlineKeyboardButton(text=button_info[0], callback_data=button_info[1])

        keyboard.add(btn)

    return keyboard


def create_reply_keyboard(buttons_text, row_width=2, resize=True, one_time=False):
    """Universal reply keyboard yaratish funksiyasi"""
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=resize,
        one_time_keyboard=one_time,
        row_width=row_width
    )

    buttons = [KeyboardButton(text) for text in buttons_text]
    keyboard.add(*buttons)

    return keyboard


# Eski funksiyalar uchun alias (orqaga moslashuv)
def get_obuna_keyboard(channels, lang='uz'):
    """Eski nom bilan obuna klaviaturasi"""
    return get_subscribe_button(channels, lang)