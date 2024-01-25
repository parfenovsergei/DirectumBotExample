import constants as keys
from telegram.ext import *
from telegram import *
import telegram
import requests
import prettytable as pt
import base64
import io

print("Script started...")

#обработчик команды /start
async def start_command(update, context):
    #создание объекта бота, keys.API_KEY - токен бота
    bot = telegram.Bot(token=keys.API_KEY)
    #получаем чат ИД пользователя и бота
    chatId = update.message.chat.id
    #создаем кнопку, в параметр text записываем текст, который мы хотим видеть в кнопке
    #параметр request_contact=True означает, что нажав кнопку пользователь отправит свой контакт
    contact_keyboard = telegram.KeyboardButton(text="Отправить контакт", request_contact=True)
    #создаем клавиатуру, параметрами прокидывается кнопка
    reply_markup = telegram.ReplyKeyboardMarkup([[contact_keyboard]])
    #теперь отправляем через бота сообщение пользователю
    #прокидывая текст сообщения и созданную клавиатуру 
    await bot.send_message(
        chat_id = chatId,
        text = "Для регистрации в чат-боте необходимо отправить контакт.",
        reply_markup = reply_markup)
    return

#обработчик команды /myorganizations
async def get_organizations(update, context):
    chatId = str(update.message.chat.id)
    url = f'{keys.DIRECTUM_PROTOCOL}://{keys.DIRECTUM_HOST}/Integration/odata/TelegramBot/GetBusinessUnitsListByUser(telegramId=\'{chatId}\')'
    try:
        authorization = base64.b64encode(bytes(keys.LOGIN + ':' + keys.PASSWORD, 'utf-8')).decode('utf-8')
        response = requests.get(
            url,
            headers = {
                'Authorization': f'Basic {authorization}'
            }
        )
        #если 400 код ответа, выводим сообщение ошибке
        if(response.status_code == 400):
            temp = response.text.replace("\"", "")
            await update.message.reply_text(temp)
            return
        #в data_list получаем массив организаций
        data_list = response.json()['value']
        reply_text = 'Ваши организации:'       
        for item in data_list:
            reply_text += "\n"
            reply_text += item['Name']
        await update.message.reply_text(reply_text)
    except:
        return 


#обработчик отправки контакта
async def send_contact_command(update, context):
    #получаем чат ИД пользователя и бота
    chatId = str(update.message.chat.id)
    #получаем номер телефона, который отправил пользователь
    phone_number = str(update.message.contact.phone_number)
    #здесь есть очень важный момент, когда человек отправляет контакт с ПК и с телефона
    #в одном из случаев phone_number содержит '+', в другом же - нет
    #поэтому перед отправкой в Directum проводим небольшие манипуляции
    is_have_plus = phone_number.startswith('+')
    if(is_have_plus):
        phone_number = phone_number.removeprefix("+")
    #создаем body
    data = { 'PhoneNumber': phone_number, 'TelegramId': chatId }
    #url для запроса
    url = f'{keys.DIRECTUM_PROTOCOL}://{keys.DIRECTUM_HOST}/Integration/odata/TelegramBot/SignUp'
    #отправляем запрос в Directum
    #authorization - логин:пароль от Serivce User преобразованный в base64
    try:
        authorization = base64.b64encode(bytes(keys.LOGIN + ':' + keys.PASSWORD, 'utf-8')).decode('utf-8')
        response = requests.post(
            url = url,
            json = data,
            headers = {
                'Authorization': f'Basic {authorization}'
            }
        )
        #204 код в нашем случае успешная регистрация, отправляем сообщение и удаляем клавиутуру у пользователя
        if(response.status_code == 204):
            await update.message.reply_text("Вы успешно зарегистрировались!", reply_markup=telegram.ReplyKeyboardRemove(True))
        #иначе выводим сообщение об ошибке и также удаляем клавиатуру
        else:
            temp = response.text.replace("\"", "")
            await update.message.reply_text(temp, reply_markup = telegram.ReplyKeyboardRemove(True))
    except:
        return
    
#функция запуска бота
def main(): 
    #с помощью библотеки telegram создаем приложение бота 
    app = Application.builder().token(keys.API_KEY).build()
    #добавляем в бота обработчики команды /start, /myorganizations и отправки контакта, подвязывая к ним созданные рание функции
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("myorganizations", get_organizations))
    app.add_handler(MessageHandler(filters.CONTACT, send_contact_command))
    #запускаем приложение, теперь происходит опрос обновлений в боте
    app.run_polling()
    
main()