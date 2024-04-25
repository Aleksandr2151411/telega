import logging

import aiohttp
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler
import datetime
from random import randrange
from config import BOT_TOKEN

TIMER = 5

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger = logging.getLogger(__name__)

reply_keyboard = [['/start', '/help'], ['/dialog', '/anek'], ['/date', '/time']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
ANEKI = [
    '''- Доктор, у меня нос чешется.
- Мой чаще.
- Нет, мой!''',
    '''Заходит улитка в бар, заказывает виски с колой, а бармен берёт и выбрасывает её из бара.
Проходит месяц, улитка снова заползает в этот бар и говорит бармену:
- Ну и зачем ты это сделал?''',
    '''Папа-кенгуру говорит маме-кенгуру:
- Давай заведём ещё одного ребёнка.
- Ты чего? Двое кенгурят мне не по карману!''',
    '''Приходит мужик к доктору и говорит: 
- Доктор, помогите, все болит. Сюда пальцем ткну - больно, сюда пальцем ткну - больно, сюда пальцем ткну - тоже больно...
Доктор: 
- Дебил, у тебя же палец сломан.'''
         ]
months = ['', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']


async def echo(update, context):
    await update.message.reply_text('Прости, но я тебя не понимаю, введи /help, чтобы посмотреть список команд.')


async def close_keyboard(update, context):
    await update.message.reply_text(
        f"ОК", reply_markup=ReplyKeyboardRemove()
    )


async def start(update, context):
    user = update.effective_user
    await update.message.reply_text(
        rf"Привет, {user.username}! Я Globus!", reply_markup=markup
    )


async def help(update, context):
    await update.message.reply_text("""Смотри, что я умею:
    /geo + <место> - показать желаемое место на карте
    /dialog - поболтать с тобой
    /anek - случайный анекдот
    /time - подскажу, который час
    /date - напомню дату""")


async def time(update, context):
    t = str(datetime.datetime.now().time())[:5]
    await update.message.reply_text(f"Точное время - {t[:2]} часов {t[3:]} минут.")


async def date(update, context):
    d = str(datetime.date.today()).split('-')
    await update.message.reply_text(f'Сегодня {d[2]} {months[int(d[1])]} {d[0]} года.')


async def anek(update, context):
    await update.message.reply_text(ANEKI[randrange(0, len(ANEKI))])


async def dialog(update, context):
    await update.message.reply_text(
        """Что ж, давай поговорим.
Если надоест, введи команду /stop.
Какое твоё любимое животное?"""
    )
    return 1


async def first_response(update, context):
    context.user_data['local'] = update.message.text
    dopstroka = ''
    if context.user_data['local'].lower() in ['кот', 'кошка', 'киса', 'кошечка', 'котик', 'kitty cat', 'котейка', 'кiт']:
        dopstroka = ' тоже'
    await update.message.reply_text(
        f"""{context.user_data['local']}?
О, а я{dopstroka} котов люблю, они милые)
Какой твой любимый цвет?"""
    )
    return 2


async def second_response(update, context):
    context.user_data['data'] = update.message.text
    await update.message.reply_text(
        f"""{context.user_data['data']}? Неплохо, 
искренне желаю, чтобы в твоей жизни появился {context.user_data['data'].lower()} {context.user_data['local'].lower()}!
Кстати, а где ты живёшь?"""
    )
    return 3


async def third_response(update, context):
    context.user_data['dota'] = update.message.text
    if 'калуг' in context.user_data['dota'].lower() or 'kalug' in context.user_data['dota'].lower():
        te = 'Круто! Я тоже в Калуге живу! Может встретимся однажды... А хотя подожди... Я же телеграм-бот...'
    else:
        te = f"""{context.user_data['dota'].capitalize()}, говоришь? 
Хочешь, я покажу тебе твоё место жительства на карте?
Просто введи /geo + нужное тебе место."""
    await update.message.reply_text(te)
    return ConversationHandler.END


async def stop(update, context):
    await update.message.reply_text("Ну ладно... Поговорим в другой раз.")
    return ConversationHandler.END


conv_handler = ConversationHandler(
    entry_points=[CommandHandler('dialog', dialog)],

    states={
        1: [MessageHandler(filters.TEXT & ~filters.COMMAND, first_response)],
        2: [MessageHandler(filters.TEXT & ~filters.COMMAND, second_response)],
        3: [MessageHandler(filters.TEXT & ~filters.COMMAND, third_response)]
    },
    fallbacks=[CommandHandler('stop', stop)]
)


def get_ll_spans(toponym):
    if not toponym:
        return (None, None)
    toponym_coodrinates = toponym["Point"]["pos"]
    toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")
    ll = ",".join([toponym_longitude, toponym_lattitude])
    envelope = toponym["boundedBy"]["Envelope"]
    l, b = envelope["lowerCorner"].split(" ")
    r, t = envelope["upperCorner"].split(" ")
    dx = abs(float(l) - float(r)) / 2.0
    dy = abs(float(t) - float(b)) / 2.0
    span = f"{dx},{dy}"
    return ll, span


async def get_response(geocoder_url, params):
    async with aiohttp.ClientSession() as session:
        async with session.get(geocoder_url, params=params) as response:
            return await response.json()


async def geocoder(update, cotext):
    zapros = update.message.text[5:]
    c = 0
    for i in zapros.lower():
        if i in 'qwertyuiopasdfghjklzxcvbnmёйцукенгшщзхъфывапролджэячсмитьбю':
            c += 1
    if update.message.text[5:] == '' or c == 0:
        await update.message.reply_text("Некорректный запрос!")
    geocoder_url = "http://geocode-maps.yandex.ru/1.x/"
    response = await get_response(geocoder_url, params={
        "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
        "format": "json",
        "geocode": update.message.text[5:]
    })

    if response["response"]["GeoObjectCollection"]["featureMember"] == []:
        await update.message.reply_text("Че-т я такого места не знаю, напиши более корректно, пожалуйста.")
    else:

        toponym = response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]

        ll, spn = get_ll_spans(toponym)

        static_api_request = f"http://static-maps.yandex.ru/1.x/?ll={ll}&spn={spn}&l=map"
        if "description" in toponym:
            de = toponym["description"]
        else:
            de = 'планета Земля'
        cap = f'''Смотри, что нашёл. Это же {toponym["name"]}, {de}! 
Я тут был однажды... проездом.
Для справки: тип объекта - {toponym["metaDataProperty"]["GeocoderMetaData"]["kind"]}.'''
        if 'калуг' in update.message.text.lower() or 'kalug' in update.message.text.lower():
            cap = "Нашёл! О, кстати, здесь меня написали."
        await cotext.bot.send_photo(
            update.message.chat_id,
            static_api_request,
            caption=cap
        )


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, echo)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("anek", anek))
    application.add_handler(CommandHandler("time", time))
    application.add_handler(CommandHandler("date", date))
    application.add_handler(CommandHandler("close", close_keyboard))
    application.add_handler(CommandHandler("geo", geocoder))

    application.add_handler(conv_handler)
    application.add_handler(text_handler)

    application.run_polling()


if __name__ == '__main__':
    main()