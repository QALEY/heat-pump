import os
import logging
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ApplicationBuilder, ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Состояния разговора
LANG, OBJ_TYPE, TOTAL_SQ, ROOM_DIM, MEDIA, PHONE = range(6)

# Тексты для мультиязычности
TEXTS = {
    'uz': {
        'welcome': "Assalomu alaykum! Issiqlik nasosi bo'yicha buyurtma berish botiga xush kelibsiz. Tilni tanlang:",
        'obj_prompt': "Ob'ekt turini tanlang yoki yozib yuboring:",
        'objects': ['Uy', 'Issiqxona', 'Bog‘cha', 'Maktab', 'Klinika', 'Kasalxona', 'Fermа', 'Zavod', 'Tashkilot', 'Boshqa'],
        'sq_prompt': "Umumiy maydonni kiriting (masalan, 150 m²):",
        'dim_prompt': "Xona o'lchamlarini kiriting (Eni x Uzunligi x Balandligi, masalan: 5x8x3) yoki o'tkazib yuborish uchun /skip deb yozing:",
        'media_prompt': "Iltimos, ob'ekt sxemasini, rasmlarini, videosini yoki ovozli xabaringizni yuboring:",
        'phone_prompt': "Oxirgi qadam: Telefon raqamingizni yuboring (tugmani bosing):",
        'phone_btn': "📱 Telefon raqamni yuborish",
        'thanks': "Rahmat! Ma'lumotlaringiz qabul qilindi. Tez orada mutaxassislarimiz siz bilan bog'lanadi."
    },
    'ru': {
        'welcome': "Здравствуйте! Добро пожаловать в бот по подбору тепловых насосов. Выберите язык:",
        'obj_prompt': "Выберите тип объекта или введите свой вариант:",
        'objects': ['Дом', 'Теплица', 'Детский сад', 'Школа', 'Клиника', 'Больница', 'Ферма', 'Завод', 'Организация', 'Другое'],
        'sq_prompt': "Введите общую площадь объекта (например, 150 м²):",
        'dim_prompt': "Введите размеры комнат (Ширина x Длина x Высота, например: 5x8x3) или отправьте /skip:",
        'media_prompt': "Пожалуйста, отправьте схему объекта, фотографии, видео или голосовое сообщение с описанием:",
        'phone_prompt': "Последний шаг: Поделитесь вашим номером телефона (нажмите кнопку ниже):",
        'phone_btn': "📱 Поделиться номером",
        'thanks': "Спасибо! Ваши данные приняты. Скоро с вами свяжутся наши специалисты."
    },
    'en': {
        'welcome': "Hello! Welcome to the heat pump consultation bot. Select language:",
        'obj_prompt': "Select the object type or type your own:",
        'objects': ['Home', 'Greenhouse', 'Kindergarten', 'School', 'Clinic', 'Hospital', 'Farm', 'Plant', 'Organization', 'Other'],
        'sq_prompt': "Enter total square meters (e.g., 150 sqm):",
        'dim_prompt': "Enter room dimensions (Width x Length x Height, e.g.: 5x8x3) or type /skip:",
        'media_prompt': "Please send the object layout scheme, photos, video, or a voice message describing the details:",
        'phone_prompt': "Final step: Share your phone number by clicking the button below:",
        'phone_btn': "📱 Share Phone Number",
        'thanks': "Thank you! Your data has been received. Our specialists will contact you shortly."
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇺🇿 O'zbek", callback_data='uz'),
         InlineKeyboardButton("🇷🇺 Русский", callback_data='ru'),
         InlineKeyboardButton("🇬🇧 English", callback_data='en')]
    ]
    await update.message.reply_text(TEXTS['ru']['welcome'], reply_markup=InlineKeyboardMarkup(keyboard))
    return LANG

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data
    context.user_data['lang'] = lang
    
    t = TEXTS[lang]
    buttons = [[KeyboardButton(obj)] for obj in t['objects']]
    keyboard = ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)
    
    await query.message.reply_text(t['obj_prompt'], reply_markup=keyboard)
    return OBJ_TYPE

async def get_object_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['obj_type'] = update.message.text
    lang = context.user_data.get('lang', 'ru')
    
    await update.message.reply_text(TEXTS[lang]['sq_prompt'])
    return TOTAL_SQ

async def get_total_square(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['total_sq'] = update.message.text
    lang = context.user_data.get('lang', 'ru')
    
    await update.message.reply_text(TEXTS[lang]['dim_prompt'])
    return ROOM_DIM

async def get_room_dim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['room_dim'] = update.message.text
    lang = context.user_data.get('lang', 'ru')
    
    await update.message.reply_text(TEXTS[lang]['media_prompt'])
    return MEDIA

async def get_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Сохраняем информацию о том, что медиа получено (фото, видео или голос)
    if 'media' not in context.user_data:
        context.user_data['media'] = []
    
    if update.message.photo:
        context.user_data['media'].append("Фото получено")
    elif update.message.video:
        context.user_data['media'].append("Видео получено")
    elif update.message.voice:
        context.user_data['media'].append("Голосовое сообщение получено")
    elif update.message.document:
        context.user_data['media'].append("Схема/Документ получен")
        
    lang = context.user_data.get('lang', 'ru')
    t = TEXTS[lang]
    
    keyboard = [[KeyboardButton(t['phone_btn'], request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(t['phone_prompt'], reply_markup=reply_markup)
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.contact.phone_number if update.message.contact else update.message.text
    context.user_data['phone'] = phone
    
    lang = context.user_data.get('lang', 'ru')
    t = TEXTS[lang]
    
    # Сводка данных для отправки менеджеру
    summary = (
        f"🚨 **Новая заявка с теплового насоса!**\n\n"
        f"🌐 Язык: {lang.upper()}\n"
        f"🏢 Объект: {context.user_data.get('obj_type')}\n"
        f"📐 Площадь: {context.user_data.get('total_sq')}\n"
        f"📏 Размеры комнат: {context.user_data.get('room_dim')}\n"
        f"📞 Телефон: {phone}"
    )
    
    # Сюда можно добавить отправку в чат менеджера или сохранение в Google Sheets
    # Например, отправка в ваш личный Telegram ID:
    # await context.bot.send_message(chat_id="ВАШ_TELEGRAM_ID", text=summary, parse_mode="Markdown")

    await update.message.reply_text(t['thanks'])
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Диалог отменен. Нажмите /start для начала заново.")
    return ConversationHandler.END

def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN", "ВСТАВЬТЕ_ТОКЕН_БОТА_ЗДЕСЬ")
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LANG: [CallbackQueryHandler(set_language)],
            OBJ_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_object_type)],
            TOTAL_SQ: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_total_square)],
            ROOM_DIM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_room_dim)],
            MEDIA: [MessageHandler(filters.PHOTO | filters.VIDEO | filters.VOICE | filters.Document.ALL, get_media)],
            PHONE: [MessageHandler(filters.CONTACT | filters.TEXT, get_phone)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    app.add_handler(conv_handler)
    # app.print_and_error_handler()
    app.run_polling()

if __name__ == '__main__':
    from telegram.ext import CallbackQueryHandler
    main()
