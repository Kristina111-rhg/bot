import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, MessageHandler, filters
import requests
from bs4 import BeautifulSoup
import aiohttp
from telegram.ext import CallbackQueryHandler


# Словарь с альтернативными написаниями названий компаний
company_names_alternatives = {
    "агентство развития платежных систем": ["арпс", "агентство развития систем", "arps.pro"],
    "аиса ит-сервис": ["аиса", "аиса ит", "аиса ит сервис", "aisa"],
    "амт-групп": ["amt-group", "амтгрупп", "amtgroup", "амт"],
    "асб": ["asb", "асб"],
    "асф-развитие": ["asf-development", "асфразвитие", "asfdevelopment"],
    "аэроб": ["aerob", "аэроб"],
    "геоскан": ["geoscan", "геоскан", "гео скан"],
    "грань новые технологии": ["gran-new-technologies", "граньновыетехнологии", "grantech", "грань технологии"],
    "датана": ["datana", "датана"],
    "ем групп": ["em-group", "емгрупп", "emgroup", "ем груп"],
    "идм плюс": ["idm-plus", "идмплюс", "idmplus", "идм", "идм+"],
    "инжиниринг+": ["engineering+", "инжиниринг", "engineeringplus", "инжениринг", "инженеринг"],
    "иннодрайв": ["innodrive", "инодрайв", "innodrive", "инодрайв"],
    "интеллект университет": ["intellect-university", "интеллектуниверситет", "intellectuniversity", "интелект"],
    "интэк промышленные системы": ["intek-industrial-systems", "интэкпромышленныесистемы", "inteksystems", "интек системы"],
    "навиа": ["navia", "навия"],
    "научные развлечения": ["scientific-entertainment", "научныеразвлечения", "sciencefun"],
    "нии \"квант\"": ["nii-quant", "нииквант", "niikvant", "нии квант", "квант нии"],
    "нииас": ["nias", "ниас"],
    "ниима \"прогресс\"": ["niima-progress", "ниимапрогресс", "niimaprogress", "нима прогрес", "ниима прогресс", "прогресс", "нима-прогресс"],
    "нпк \"антей\"": ["npc-antey", "нпкантей", "npcantey", "антей", "нпк антей", "нпк-антей"],
    "нпо андроидная техника": ["npo-android-technology", "нпоандроиднаятехника", "npoandroidtech", "андроидная техника"],
    "ньюлинк": ["newlink", "нюлинк"],
    "омега": ["omega", "омега"],
    "петроградская лаборатория": ["petrograd-laboratory", "петроградскаялаборатория", "petrolab", "лаборатория"],
    "позитрон-энерго": ["positron-energy", "позитронэнерго", "positronenergo", "позитрон", "позитрон энерго"],
    "промобит": ["promobit", "промабит"],
    "промтехника-приволжье": ["promtechnika-volga", "промтехникаприволжье", "приволжье", "promtechvolga"],
    "проф-ит": ["prof-it", "профит", "profit", "проф ИТ"],
    "рнд мгту": ["rnd-mstu", "рндмгту", "rndmstu", "мгту"],
    "роббо": ["robbo", "робо"],
    "сибаэрокрафт": ["sibaerocraft", "сибаэрокрафт"],
    "синапс": ["synapse", "синапс"],
    "смарткор": ["smartcore", "смарт кор"],
    "стрим лабс": ["stream-labs", "стримлабс", "streamlabs", "стрим-лабс"],
    "техноред": ["technored", "техно ред"],
    "уникальные роботы": ["unique-robots", "уникальныероботы", "uniquerobots"],
    "урц \"альфа-интех\"": ["urc-alpha-intech", "урцальфаинтех", "urcalphaintech", "альфа интех", "альфаинтех" "урц альфа интех"],
    "цифровой альянс": ["digital-alliance", "цифровойальянс", "digitalalliance"]
}

# Функция для нормализации названия компании и поиска альтернативных написаний
def normalize_company_name(name):
    name = name.lower()
    for key, alternatives in company_names_alternatives.items():
        if name in alternatives:
            return key
    return name

# Логирование для отслеживания ошибок
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)  # Используем name, чтобы получить имя текущего модуля

# Токен бота
TOKEN = "7303719671:AAFGF-tzPJRwavGHjm0RsyO1IKQFHwqju0A"

# Создайте Application
application = ApplicationBuilder().token(TOKEN).build()

events = [
    {
        "date": "2024-06-26",
        "event": "TECH WEEK 2024",
        "place": "Москва, Технопарк «Сколково».",
        "url": "https://techweek.moscow/",
        "description": "Tech Week 2024 — это конференция об инновационных технологиях для решения задач бизнеса. Погрузитесь в мир цифровых технологий для бизнеса."
    },
    {
        "date": "2024-07-08",
        "event": "ИННОПРОМ",
        "place": "Екатеринбург, Свердловская обл., Россия.",
        "url": "https://innoprom.com/",
        "description": "«Иннопром» является главным в России мероприятием, посвященным новейшим технологиям и разработкам в сфере промышленности, а также главной экспортной площадкой для российских промышленных компаний."
    },
    {
        "date": "2024-08-01",
        "event": "Армия 2024",
        "place": "Московская область, Московская обл., Россия.",
        "url": "https://army2024.ru/",
        "description": "АРМИЯ2024 X Международный военно-технический Форум «Армия»."
    }
    # Добавьте больше событий здесь
]

# Функция для форматирования информации о компании
def format_company_info(info):
    # Заменяем названия полей на подчеркнутые и добавляем жирный шрифт к заголовкам
    info = info.replace("Телефон", "<u>Телефон</u>")
    info = info.replace("E-mail", "<u>E-mail</u>")
    info = info.replace("Сайт", "<u>Сайт</u>")
    info = info.replace("Юридический адрес", "<u>Юридический адрес</u>")
    info = info.replace("Название:", "<b>Название:</b>")
    info = info.replace("Информация:", "<b>Информация:</b>")
    info = info.replace("Контакты, связанные с компанией:", "<b>Контакты, связанные с компанией:</b>")
    return info

# Функция для получения событий
def get_events():
    return events

# Функция для создания кнопок событий с URL
def build_event_buttons(events_list):
    keyboard = []
    for event in events_list:
        event_button = [InlineKeyboardButton(event['event'], url=event['url'])]
        keyboard.append(event_button)
    return InlineKeyboardMarkup(keyboard)

# Функция для обработки команды "/calendar"
async def calendar(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    logger.info("Received /calendar command")
    events_list = get_events()
    text = ""
    for event in events_list:
        text += (
            f"<b>Событие:</b> {event['event']}\n"
            f"<b>Дата:</b> {event['date']}\n"
            f"<b>Место:</b> {event['place']}\n"
            f"<b>Описание:</b> {event['description']}\n\n"
        )
    await query.message.reply_text(text, parse_mode='HTML')
    reply_markup = build_event_buttons(events_list)
    await query.message.reply_text('Выберите событие:', reply_markup=reply_markup)

# Функция для обработки команды "/start"
async def start(update: Update, context: CallbackContext) -> None:
    logger.info("Received /start command")
    command_buttons = build_command_buttons()
    await update.message.reply_text(
        "<b>Привет! Я бот Консорциума робототехники. Что ты хочешь сделать?</b>",
        parse_mode='HTML',
        reply_markup=command_buttons
    )

# Функция для создания кнопок команд, включая новую кнопку "Узнать информацию о компании"
def build_command_buttons():
    keyboard = [
        [InlineKeyboardButton("Календарь событий", callback_data='calendar')],
        [InlineKeyboardButton("Чат Консорциума", callback_data='chat')],
        [InlineKeyboardButton("Узнать информацию о членах Консорциума", callback_data='company_info')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Функция для обработки callback_query от кнопок
async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == 'calendar':
        await calendar(update, context)
    elif query.data == 'chat':
        await chat(update, context)
    elif query.data == 'company_info':
        # Отправляем новое сообщение с запросом ввести название компании
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Введите название компании:"
        )

# Функция для обработки текстовых сообщений и получения информации о компании
async def company_info(update: Update, context: CallbackContext) -> None:
    text = update.message.text.lower()
    normalized_name = normalize_company_name(text)
    url = f"https://project9674621.tilda.ws/"  # Замените URL на реальный адрес поиска компаний
    html = await get_html(url)
    if html:
        companies = await parse_companies(html)
        company_data = companies.get(normalized_name)  # Используйте нормализованное имя для поиска
        if company_data:
            # Разделение информации на основные данные и контакты
            main_info, contacts_info = split_company_data(company_data['info'])
            
            # Форматирование и отправка основной информации о компании
            formatted_main_info = format_company_info(
                f"<b>Название:</b> {company_data['name']}\n"
                f"<b>Информация:</b>\n{main_info}"
            )
            await update.message.reply_text(formatted_main_info, parse_mode='HTML')

            # Форматирование и отправка контактов, связанных с компанией
            if contacts_info:
                formatted_contacts_info = format_company_info(
                    f"<b>Контакты, связанные с компанией:</b>\n{contacts_info}"
                )
                await update.message.reply_text(formatted_contacts_info, parse_mode='HTML')

# Функция для разделения информации о компании на основные данные и контакты
def split_company_data(info):
    # Предположим, что контакты отделены строкой "Контакты, связанные с компанией"
    parts = info.split("Контакты, связанные с компанией")
    main_info = parts[0].strip()
    contacts_info = parts[1].strip() if len(parts) > 1 else ""
    return main_info, contacts_info

# Асинхронная функция для получения HTML страницы
async def get_html(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.text()
            return None

# Функция для парсинга информации о компаниях
async def parse_companies(html):
    soup = BeautifulSoup(html, 'html.parser')
    companies = {}
    # Убедитесь, что отступы согласованы внутри блока 'for'
    for company_div in soup.find_all('div', class_='t232__title t-name t-name_lg'):
        name = company_div.text.strip()
        info_div = company_div.find_next('div', class_='t-row').find('div', class_='t-col t-col_8 t-prefix_2 t-align_left')
        if info_div:
            info = info_div.get_text(separator='\n').strip()
            companies[name.lower()] = {
                'name': name,
                'info': info
            }
    logger.info(f"Parsed companies: {companies}")
    return companies

# Функция для обработки команды "/chat"
async def chat(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    logger.info("Received /chat command")
    keyboard = [
        [InlineKeyboardButton("Чат @hjbnljibui", url='https://t.me/hjbnljibui')],
        [InlineKeyboardButton("Чат @hjfnvanjre", url='https://t.me/hjfnvanjre')],
        [InlineKeyboardButton("Новый Чат", url='https://t.me/+TkYr_wt4jVc0NDYy')]  # Добавлена новая кнопка
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text('Выберите чат:', reply_markup=reply_markup)

# Регистрация обработчиков напрямую в application
application.add_handler(CommandHandler('start', start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, company_info))
application.add_handler(CallbackQueryHandler(button))

# Запуск бота
if __name__ == '__main__':
    logger.info("Starting bot...")
    application.run_polling()