from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
from aiogram import types

from keyboards.default.keyboards import get_subscribe_button
from utils.db_api.database import Database
from handlers.users.start import check_user_subscription

class SubscriptionMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message: types.Message, data: dict):
        db = Database()
        channels = db.get_all_channels()
        subscribed = await check_user_subscription(message.bot, message.from_user.id, channels)
        if not subscribed:
            lang = 'uz'  # Yoki db.get_user_lang(message.from_user.id)
            texts = {
                'uz': "📢 Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
                'ru': "📢 Подпишитесь на следующие каналы для использования бота:",
                'en': "📢 Subscribe to the following channels to use the bot:"
            }
            await message.answer(
                texts.get(lang, texts['uz']),
                reply_markup=get_subscribe_button(channels, lang)
            )
            raise CancelHandler()  # ❌ Boshqa handlerlar ishlamaydi

    async def on_pre_process_callback_query(self, callback: types.CallbackQuery, data: dict):
        db = Database()
        channels = db.get_all_channels()
        subscribed = await check_user_subscription(callback.bot, callback.from_user.id, channels)
        if not subscribed:
            lang = 'uz'
            texts = {
                'uz': "📢 Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
                'ru': "📢 Подпишитесь на следующие каналы для использования бота:",
                'en': "📢 Subscribe to the following channels to use the bot:"
            }
            await callback.message.answer(
                texts.get(lang, texts['uz']),
                reply_markup=get_subscribe_button(channels, lang)
            )
            raise CancelHandler()
