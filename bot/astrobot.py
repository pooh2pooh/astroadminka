#
#
# Все циклы находятся в data/cycles и идентификатором является имя файла json.
#
# В data/replys ответы бота, принцип тот-же, идентификатором является имя файла json,
# если в файле меню не указать никаких кнопок, автоматически добавиться return_button_disallow_delete_msg,
# это означает что нажатие в этом меню кнопки Главное меню откроет его, но не удалит это сообщение!
#
# В data/users файлы профилей пользователей, имя файла это id пользователя в telegram,
# название полей профиля являются идентификаторами за некоторыми исключениями (типо location вместо latitude и longitude),
# set_название_поля_профиля — это кнопка для обновления этого поля.
#
#
# Версия Астробота 2.0
#

#
# ВАЖНОЕ СООБЩЕНИЕ! (ДЛЯ РАЗРАБОТЧИКОВ)
#
# После ДОБАВЛЕНИЯ НОВЫХ ПОЛЕЙ В ПРОФИЛЬ пользователя,
# необходимо СВЕРИТЬ ИТОГОВОЕ СОСТОЯНИЕ с функциями:
#
# create_or_load_user_data — здесь см. template, шаблон нового профиля
# is_completed_profile — здесь см. keys_to_skip, поля которые не нужно учитывать при заполнении пользователем профиля
#
#
# ДОП. ВОЗМОЖНОСТИ:
#
# В файлах циклов data/cycles/*.json можно использовать параметр icon: <bootstrap icon name, без классификатора типо bi>
# для отображение иконки у цикла в меню админки
#

import os
import sys
import re
import json
from telebot.async_telebot import AsyncTeleBot
import telebot
from datetime import datetime, timedelta, timezone
import requests
import pytz
import math
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import random


# Настройки бота
cycles_dir = '../data/cycles' # циклы
users_dir  = '../data/users' # пользователи
replys_dir = '../data/replys' # ответы бота
subscriptions_dir = '../data/subscriptions' # подписки (тарифы)
activity_dir = '../data/activity_data' # понедельная статистика использования сервиса

return_button = telebot.types.InlineKeyboardButton(text='Главное меню', callback_data='main_menu') # Кнопка возврата в меню
return_button_disallow_delete_msg = telebot.types.InlineKeyboardButton(text='Главное меню', callback_data='main_menu_for_not_delete_msg') # Кнопка возврата в меню без удаления исходного сообщения


system_message_ids = {} # тут сохраняем id системного сообщения которое нужно удалить после выполнения действий пользователем


#
# Экранируем спец символы для использования форматирования MarkdownV2 в циклах (сервисах)
def escape_markdown(text):
    special_chars = r'-.!)('
    escaped_text = ''
    underscore_count = 0  # Счетчик подчеркиваний
    for char in text:
        if char in special_chars:
            escaped_text += '\\' + char
            if underscore_count >= 3:
                escaped_text += '—' * underscore_count  # Заменяем подчеркивания на столько же подчеркиваний
                underscore_count = 0  # Обнуляем счетчик
        elif char == '_':
            underscore_count += 1  # Увеличиваем счетчик подчеркиваний
        else:
            if underscore_count >= 3:
                escaped_text += '—' * underscore_count  # Заменяем подчеркивания, если их количество больше или равно 3
            escaped_text += char
            underscore_count = 0  # Обнуляем счетчик при обнаружении другого символа
    if underscore_count >= 3:
        escaped_text += '—' * underscore_count  # Заменяем последние подчеркивания, если их количество больше или равно 3
    return escaped_text.replace('**', '*')


#
# Считаем активность пользователей (команд в день)
def update_week_activity_data():
    # Определяем текущую дату
    current_date = datetime.now()
    week_number = int(current_date.strftime("%U")) + 1  # Номер текущей недели, начиная с 1
    year = current_date.year  # Год текущей недели
    
    # Создаем или загружаем файл данных текущей недели
    week_activity_file = os.path.join(activity_dir, f'week_{year}_{week_number}_activity.json')
    if os.path.exists(week_activity_file):
        with open(week_activity_file, 'r', encoding='utf-8') as f:
            week_activity_data = json.load(f)
    else:
        week_activity_data = {}
        for day in ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']:
            week_activity_data[day] = 0
    
    # Обновляем счетчик для текущего дня недели
    russian_days = {
        "Monday": "Понедельник",
        "Tuesday": "Вторник",
        "Wednesday": "Среда",
        "Thursday": "Четверг",
        "Friday": "Пятница",
        "Saturday": "Суббота",
        "Sunday": "Воскресенье"
    }

    current_week_day = current_date.strftime('%A')
    if russian_days.get(current_week_day) in week_activity_data:
        week_activity_data[russian_days[current_week_day]] += 1
    
    # Сохраняем обновленные данные обратно в файл
    with open(week_activity_file, 'w', encoding='utf-8') as f:
        json.dump(week_activity_data, f, ensure_ascii=False)


#
# Получаем локальное время для пользователя, в его часовом поясе
async def get_local_time(user_timezone_offset):
    # Разбиваем строку на части для определения смещения
    parts = user_timezone_offset.split('+')
    if len(parts) == 1:  # Если символ '+' не найден, ищем '-'
        parts = user_timezone_offset.split('-')
        sign = -1
    else:
        sign = 1

    hours = int(parts[1])
    # Вычисляем смещение в минутах
    offset_minutes = hours * 60 * sign

    # Получаем объект часового пояса пользователя
    user_tz = pytz.FixedOffset(offset_minutes)

    # Получаем текущее время в UTC
    utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)

    # Конвертируем в локальное время пользователя
    user_now = utc_now.astimezone(user_tz).replace(microsecond=0)

    return user_now


#
# Получаем время восхода, захода солнца по API (и другие данные)
async def get_sunrise_sunset(user, date):
    await bot.send_chat_action(user['user_id'], 'typing')  # Установка статуса "печатает..."

    url = "https://api.sunrise-sunset.org/json"

    timezones = {
        "GMT+3": "Europe/Moscow"
    }

    params = {
        "lat": user['latitude'],
        "lng": user['longitude'],
        "date": date.strftime("%Y-%m-%d"),
        "formatted": 0,
        "tzid": timezones.get(user['timezone'])
    }
    response = requests.get(url, params=params)
    return response.json()


#
# Сканирует папку с файлами циклов при запуске бота,
# и сохраняет список циклов в глобальную переменную cycles
def scan_cycles():

    print('Загружаю файлы циклов…')
    cycles = []

    try:
        # Получаем список файлов циклов
        files = os.listdir(cycles_dir)

        # Перебираем файлы циклов
        for file in files:
            try:
                # Проверяем, является ли файл JSON файлом
                if file.endswith('.json'):
                    # Считываем содержимое JSON файла
                    file_path = os.path.join(cycles_dir, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        cycle = json.load(f)
                        # Добавляем циклы в список
                        cycles.append(cycle['title'])
                    print('✓ Цикл успешно загружен:', file)
            except FileNotFoundError:
                print(f'x Файл не найден: {file_path}')
            except json.JSONDecodeError:
                print(f'x Ошибка при декодировании JSON: {file_path}')
            except Exception as e:
                print(f'x Произошла ошибка: {e}')

    except Exception as e:
        print('x Произошла ошибка:', e)

    cycles_count = len(cycles)
    if cycles_count > 0:
        print('→ Все циклы успешно загружены', f"({cycles_count})")

    return cycles


#
# Проверяет существует ли профиль пользователя,
# и создаёт если нет. Выполняется по команде /start бота
async def create_or_load_user_data(user_id, start_param=False):

    print('Ищу нового пользователя в базе данных…')

    if not start_param.isdigit():
        start_param = False
    
    # Путь к файлу данных пользователя
    user_file_path = os.path.join(users_dir, f'{user_id}.json')

    try:
        # Попытка открыть файл данных пользователя
        with open(user_file_path, 'r', encoding='utf-8') as f:
            print(f'→ Нашёл профиль', user_file_path)
            user = json.load(f)

            if not await is_completed_profile(user):
                # Если файл профиля существует, но не заполнен
                system_message_ids[user_id] = await get_update_profile(user_id, user)
            else:
                # Если файл профиля существует и заполнен, возвращаем "С возвращением"
                await send_menu(user_id, 'hello')

    except FileNotFoundError:
        try:
            # Шаблон для нового файла профиля пользователя
            template = {
                "full_name": "",
                "birth_day": "",
                "birth_time": "",
                "timezone": "",
                "latitude": "",
                "longitude": "",
                "birth_place": "",
                "referals": [],
                "subscription": "",
                "cycles": []
            }

            # Если файл не существует, создаем новый
            with open(user_file_path, 'w', encoding='utf-8') as f:
                json.dump(template, f, ensure_ascii=False)
            print(f'→ Создан новый профиль пользователя', user_file_path)

            # Приветствуем нового пользователя
            if start_param == False:
                await send_menu(user_id, 'welcome')
            else:
                print(f'Пользователь {start_param} пригласил нового пользователя {user_id}')
                await send_menu(user_id, 'referal')
                await get_update_profile(user_id, field = f'ref_{start_param}')

        except Exception as e:
            # В случае ошибки при создании файла выводим сообщение об ошибке с указанием текущего файла
            print(f'x Ошибка при создании файла {user_file_path}: {e}')
            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.add(return_button)
            await bot.send_message(user_id, "❌ Упс! Что-то пошло не так, обратись в поддержку для решения проблемы", reply_markup=keyboard)


#
# Отправляет меню из файла пользователю,
# menu_id - это название файла с описанием меню,
# replace_message - если не 0, удаляет сообщение перед отправкой меню
async def send_menu(user_id, menu_id, replace_message=0, option_data=False):

    print('Пользователь', user_id, 'запросил меню', menu_id)

    try:

        user_task = asyncio.ensure_future(get_user_profile(user_id))
        user = await user_task  # Дождаться выполнения асинхронной задачи и получить результат

        reply_file_path = os.path.join(replys_dir, f'{menu_id}.json')

        # Создание inline клавиатуры кнопок для меню
        keyboard = telebot.types.InlineKeyboardMarkup()
        
        # Чтение содержимого JSON файла
        with open(reply_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Извлечение сообщения и кнопок из данных
        message = data.get('message', '')
        buttons = data.get('keyboard', [])

        # !!! <>#$%
        # Обрабатываем встроенные в сообщения перменные
        if re.search(r'\{.*?\}', message) is not None:

            if menu_id == 'referal_get_link':
                #user['user_id'] = user_id # нужен для подстановки id пользователя в реф ссылку
                bot_info = await bot.get_me()
                bot_username = bot_info.username if bot_info else 'test'
                user['ref_link_to_bot'] = f'https://t.me/{bot_username}?start={user_id}' # более универсальный способ генерации реф ссылки
            
            elif menu_id == 'subscription':
                subscription_task = asyncio.ensure_future(get_user_subscription(user['subscription'])) # подменяем идентификатор подписки на название
                subscription = await subscription_task
                user['subscription'] = subscription['title']

            elif menu_id == 'get_active_cycles':
                user['user_id'] = user_id
                user_time = await get_local_time(user['timezone'])  # получает локальное время пользователя
                # Текущая дата
                user['date'] = user_time.strftime('%d.%m.%Y')
                # Планетарный час
                # Получение ответов для вчера, сегодня и завтра и сохранение их в отдельные переменные
                planetary_clock_yesterday, planetary_clock_today, planetary_clock_tomorrow = (
                    await get_sunrise_sunset(user, user_time - timedelta(days=1)),
                    await get_sunrise_sunset(user, user_time),
                    await get_sunrise_sunset(user, user_time + timedelta(days=1))
                )
                yesterday_sunset = datetime.strptime(planetary_clock_yesterday['results']['sunset'],
                                                     "%Y-%m-%dT%H:%M:%S%z")
                sunrise = datetime.strptime(planetary_clock_today['results']['sunrise'], "%Y-%m-%dT%H:%M:%S%z")
                sunset = datetime.strptime(planetary_clock_today['results']['sunset'], "%Y-%m-%dT%H:%M:%S%z")
                tomorrow_sunrise = datetime.strptime(planetary_clock_tomorrow['results']['sunrise'],
                                                     "%Y-%m-%dT%H:%M:%S%z")
                user['planetary_clock'] = ''
                if user_time < sunrise or user_time > sunset:
                    if user_time < sunrise:
                        duration = sunrise - yesterday_sunset
                        hour_duration = duration / 12
                        relevant_time = user_time - yesterday_sunset
                        current_hour = int(relevant_time / hour_duration)
                        start = yesterday_sunset + hour_duration * current_hour
                        end = start + hour_duration
                    else:
                        duration: timedelta = tomorrow_sunrise - sunset
                        hour_duration = duration / 12
                        relevant_time = user_time - sunset
                        current_hour = int(relevant_time / hour_duration)
                        start = sunset + hour_duration * current_hour
                        end = start + hour_duration
                    user['planetary_clock'] = f'{current_hour} ({start.hour}:{start.minute} - {end.hour}:{end.minute})'
                else:
                    duration: timedelta = sunset - sunrise
                    hour_duration = duration / 12
                    relevant_time = user_time - sunrise
                    current_hour = int(relevant_time / hour_duration)
                    start = sunrise + hour_duration * current_hour
                    end = start + hour_duration
                    user[
                        'planetary_clock'] = f'{current_hour} ({start.hour}:{start.minute if start.minute >= 10 else "0" + start.minute.__str__()} - {end.hour}:{end.minute if end.minute >= 10 else "0" + end.minute.__str__()})'
                # 4х часовки
                four_hours = await cycle_manager.start(user, 'four_hours')
                user['four_hours'] = four_hours.splitlines()[0]

            elif menu_id == 'get_active_cycles_next_1':
                user_time = await get_local_time(user['timezone'])  # получает локальное время пользователя
                # Завтрашняя дата
                user_time = user_time + timedelta(days=1)
                user['date_tomorrow'] = user_time.strftime('%d.%m.%Y')

            elif menu_id == 'get_active_cycles_next_30':
                user_time = await get_local_time(user['timezone'])  # получает локальное время пользователя
                # Текущая дата
                user['date'] = user_time.strftime('%d.%m.%Y')
                user_time = user_time + timedelta(days=30)
                user['date_next_month'] = user_time.strftime('%d.%m.%Y')

            elif option_data:
                if menu_id == 'partner_show':
                    print(f'Совместимость: Загружаю {option_data['title']}')
                    message = message.format(**option_data)

            else:
                print('Не понимаю что загружать…')

            message = message.format(**user)

        # !!!2 <>#$%
        # Обрабатываем разные меню
        if menu_id == 'cycles':

            buttons_task = asyncio.ensure_future(get_cycles('Основные'))
            buttons = await buttons_task + buttons

        elif menu_id == 'cycles_personal' or menu_id == 'partner_show':

            buttons_task = asyncio.ensure_future(get_cycles('Личные'))
            buttons = await buttons_task + buttons
            if menu_id == 'partner_show':
                buttons.append({"text": '⛔️ Удалить', "callback": 'partner_del_0'})

        elif menu_id == 'cycles_investment':

            buttons_task = asyncio.ensure_future(get_cycles('Инвестиционные'))
            buttons = await buttons_task + buttons

        elif menu_id == 'cycles_sun':

            buttons_task = asyncio.ensure_future(get_cycles('Солнечные'))
            buttons = await buttons_task + buttons

        elif menu_id == 'cycles_retrogrades':

            buttons_task = asyncio.ensure_future(get_cycles('Ретрограды'))
            buttons = await buttons_task + buttons

        elif menu_id == 'prognostics':

            buttons_task = asyncio.ensure_future(get_cycles('Прогностика'))
            buttons = await buttons_task + buttons

        elif menu_id == 'my_subscription_info':

            buttons_task = asyncio.ensure_future(get_allowed_subscriptions(user['subscription']))
            buttons = await buttons_task + buttons

        elif menu_id == 'compatibility':

            buttons_task = asyncio.ensure_future(get_partner(user_id))
            buttons = await buttons_task + buttons

        row = []  # Список для кнопок в текущем ряду

        # Определяем максимальное количество кнопок в ряду в зависимости от количества кнопок
        max_buttons_per_row = 2 if len(buttons) >= 4 else 1

        for button_data in buttons:
            button_text = button_data.get('text', '')
            callback_data = button_data.get('callback', '')
            button = telebot.types.InlineKeyboardButton(text=button_text, callback_data=callback_data)
            row.append(button)
                    
            # Если набралось максимальное количество кнопок в ряду или дошли до последней кнопки
            if len(row) == max_buttons_per_row or button_data == buttons[-1]:
                keyboard.add(*row)  # Добавляем кнопки текущего ряда
                row = []  # Очищаем список для следующего ряда

        if len(keyboard.keyboard) == 0:
            keyboard.add(return_button_disallow_delete_msg)
        
        # Отправка сообщения с inline кнопками пользователю
        if replace_message == 0:
            await bot.send_message(user_id, message, reply_markup=keyboard)
        else:
            await bot.delete_message(user_id, replace_message)
            await bot.send_message(user_id, message, reply_markup=keyboard)

        print('✓ Отправил меню пользователю')
        
    except FileNotFoundError:
        print('x Не могу найти меню, которое запросил пользователь')
        keyboard.add(return_button)
        await bot.send_message(user_id, "❌ Упс! Что-то пошло не так, обратись в поддержку для решения проблемы", reply_markup=keyboard)
    except Exception as e:
        print('x Произошла ошибка:', e, '\n', 'строка ' + str(e.__traceback__.tb_lineno) + ',', __file__)
        keyboard.add(return_button)
        await bot.send_message(user_id, "❌ Упс! Случилось что-то страшное!\n\nНе переживай, обратись в поддержку для решения проблемы", reply_markup=keyboard)


#
# Проверяет полностью ли заполнен профиль пользователя. (True/False)
async def is_completed_profile(user):
    # Ключи которые не требуют заполнения от пользователя,
    # а управляются администратором например
    keys_to_skip = ['referals', 'subscription', 'cycles']
    # Вернёт False если в профиле пользователя есть неуказанная информация
    if any(value == '' for key, value in user.items() if key not in keys_to_skip):
        return False
    else:
        return True


#
# Запрашивает данные у пользователя для обновления,
# user - это объект с профилем пользователя, если он уже был запрошен (для предотвращения двойного чтения файла)
# field — это параметр профиля пользователя (когда нужно обновить один конкретный параметр профиля)
# replace_message - если не 0, удаляет сообщение перед отправкой нового
async def get_update_profile(user_id, user=False, field=False, replace_message=0):

    print(f'Проверяю профиль пользователя {user_id}…')

    if user == False:
        # Путь к файлу данных пользователя
        user_file_path = os.path.join(users_dir, f'{user_id}.json')

        with open(user_file_path, 'r', encoding='utf-8') as f:
            print(f'→ Нашёл профиль', user_file_path)
            user = json.load(f)

    system_message_id = False

    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(return_button)

    if field == False:
        if user['full_name'] == '':
            # Если пользователь не заполнял ФИО
            message = await bot.send_message(user_id, profile_editor.start_editing(user_id, "full_name"), reply_markup=keyboard)
            system_message_id = message.message_id
        elif user['birth_day'] == '':
            # Если пользователь не заполнял День рождения
            message = await bot.send_message(user_id, profile_editor.start_editing(user_id, "birth_day"), reply_markup=keyboard)
            system_message_id = message.message_id
        elif user['birth_time'] == '':
            # Если пользователь не заполнял Время рождения
            message = await bot.send_message(user_id, profile_editor.start_editing(user_id, "birth_time"), reply_markup=keyboard)
            system_message_id = message.message_id
        elif user['timezone'] == '':

            # Создание кнопок для различных часовых поясов
            time_zone_buttons = [
                ['GMT-12', 'GMT-11', 'GMT-10', 'GMT-9'],
                ['GMT-8', 'GMT-7', 'GMT-6', 'GMT-5'],
                ['GMT-4', 'GMT-3', 'GMT-2', 'GMT-1'],
                ['GMT-0', 'GMT+1', 'GMT+2', 'GMT+3'],
                ['GMT+4', 'GMT+5', 'GMT+6', 'GMT+7'],
                ['GMT+8', 'GMT+9', 'GMT+10', 'GMT+11', 'GMT+12']
            ]

            # Создание клавиатуры с кнопками часовых поясов
            keyboard = telebot.types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)  # 4 кнопки в ряду
            for row in time_zone_buttons:
                keyboard.row(*[telebot.types.KeyboardButton(text) for text in row])

            # Если пользователь не заполнял Часовой пояс
            message = await bot.send_message(user_id, profile_editor.start_editing(user_id, "timezone"), reply_markup=keyboard)
            system_message_id = message.message_id
        elif user['latitude'] == '' or user['longitude'] == '':

            # Создание клавиатуры с кнопкой для отправки геолокации
            keyboard = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
            location_button = telebot.types.KeyboardButton(text="Отправить геолокацию", request_location=True)
            keyboard.add(location_button)

            # Если пользователь не заполнял Местоположение
            message = await bot.send_message(user_id, profile_editor.start_editing(user_id, "location"), reply_markup=keyboard)
            system_message_id = message.message_id
        elif user['birth_place'] == '':
            # Если пользователь не заполнял Место рождения
            message = await bot.send_message(user_id, profile_editor.start_editing(user_id, "birth_place"), reply_markup=keyboard)
            system_message_id = message.message_id
    else:
        if field.startswith("cycle_"):
            cycle = field[len("cycle_"):]
            if cycle in user['cycles']:
                print(f'{cycle} удалён из списка подписок для {user_id}')
                profile_editor.process_input(user_id, f'cycle_remove_{cycle}')
            else:
                print(f'{cycle} добавлен в список подписок для {user_id}')
                profile_editor.process_input(user_id, f'cycle_add_{cycle}')

        elif field.startswith("ref_"):
            referal = field[len("ref_"):]
            if referal in user['referals']:
                print(f'{referal} уже есть в списке рефералов для {user_id}')
            else:
                print(f'{referal} добавлен в список рефералов для {user_id}')
                profile_editor.process_input(user_id, f'ref_add_{referal}')

        elif replace_message == 0:
            message = await bot.send_message(user_id, profile_editor.start_editing(user_id, field), reply_markup=keyboard)
            system_message_id = message.message_id
        else:
            await bot.delete_message(user_id, replace_message)
            message = await bot.send_message(user_id, profile_editor.start_editing(user_id, field), reply_markup=keyboard)
            system_message_id = message.message_id

    if system_message_id != False:
        return system_message_id
    else:
        return False


#
# Читает файл профиля пользователя и возвращает объект профиля
async def get_user_profile(user_id):

    print(f'Получаю профиль пользователя {user_id}…')
    
    # Путь к файлу данных пользователя
    user_file_path = os.path.join(users_dir, f'{user_id}.json')

    try:
        # Попытка открыть файл данных пользователя
        with open(user_file_path, 'r', encoding='utf-8') as f:
            print(f'→ Прочитано', user_file_path)
            user = json.load(f)
            return user
    except FileNotFoundError:
        print(f'x Несуществующий профиль для {user_id}')
    
    return False


#
# Читает файл подписки (тарифа) и возвращает объект подписки
async def get_user_subscription(subscription_file):

    if subscription_file == '':
        subscription_file = 'default'

    print(f'Получаю информацию о подписке {subscription_file}…')
    
    # Путь к файлу данных пользователя
    subscription_file_path = os.path.join(subscriptions_dir, f'{subscription_file}.json')

    try:
        # Попытка открыть файл данных пользователя
        with open(subscription_file_path, 'r', encoding='utf-8') as f:
            print(f'→ Прочитано', subscription_file_path)
            subscription = json.load(f)
            return subscription
    except FileNotFoundError:
        print(f'x Несуществующая подписка {subscription_file}')
    
    return False


#
# Читает файлы подписок (тарифов) и возвращает объект с кнопками
async def get_allowed_subscriptions(subscription_file):

    if subscription_file == '':
        subscription_file = 'default'

    print(f'Получаю информацию о доступных подписках, текущая {subscription_file}…')

    subscription_files = [f for f in os.listdir(subscriptions_dir) if f.endswith('.json') and f != subscription_file + '.json']

    buttons = []
    for file_name in subscription_files:
        with open(os.path.join(subscriptions_dir, file_name), 'r') as f:
            subscription_data = json.load(f)
            name = subscription_data.get('title', 'Unknown')
            price = subscription_data.get('price', 'Unknown')
            button_text = f'{name} - {price} руб/мес'
            callback_data = f'subscribe_{file_name[:-5]}'  # Убираем '.json' из имени файла
            buttons.append({"text": button_text, "callback": callback_data})

    return buttons


#
# Читает файлы партнёров (опция Совместимость) и возвращает объект с кнопками
async def get_partner(user_id, target='hash'):
    # Модуль Совместимость, получение партнёра(ов)
    partners_dir = os.path.join(users_dir, f'{user_id}/')

    if not os.path.exists(partners_dir):
        print(f'Каталог для пользователя {user_id} не найден.')
        return []

    if target == 'hash':
        print(f'Получаю информацию о партнёрах (Совместимость), для {user_id}…')
        partner_files = [f for f in os.listdir(partners_dir) if f.endswith('.json')]

        buttons = []
        for file_name in partner_files:
            file_path = os.path.join(partners_dir, file_name)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    try:
                        partner_data = json.load(f)
                        name = partner_data.get('title', 'Unknown')
                        button_text = f'{name}'
                        callback_data = f'partner_{file_name[:-5]}'  # Убираем '.json' из имени файла
                        buttons.append({"text": button_text, "callback": callback_data})
                    except json.JSONDecodeError:
                        print(f'Ошибка чтения файла {file_name}')
            else:
                print(f'Файл {file_name} не найден.')

        return buttons

    else:
        print(f'Получаю информацию о партнёре (Совместимость) — {target}, для {user_id}…')
        file_name = f'{target}.json'

        file_path = os.path.join(partners_dir, file_name)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try:
                    partner_data = json.load(f)

                except json.JSONDecodeError:
                    print(f'Ошибка чтения файла {file_name}')
        else:
            print(f'Файл {file_name} не найден.')

        return partner_data


#
# Читает файлы циклов и возвращает объект с кнопками
async def get_cycles(category):
    print(f'Получаю информацию о доступных циклах…')

    cycle_files = [f for f in os.listdir(cycles_dir) if f.endswith('.json')]

    buttons = []
    for file_name in cycle_files:
        with open(os.path.join(cycles_dir, file_name), 'r') as f:
            cycle_data = json.load(f)
            name = cycle_data.get('title', 'Unknown')
            cycle_category = cycle_data.get('category', 'Uncategorized')
            button_text = f'{name}'
            callback_data = f'cycle_{file_name[:-5]}'  # Убираем '.json' из имени файла
            if category != cycle_category:
                continue
            buttons.append({"text": button_text, "callback": callback_data})

    return buttons


#
# Запрашивает данные цикла из файла,
# user - это объект с профилем пользователя, если он уже был запрошен (для предотвращения двойного чтения файла)
# cycle — это файл цикла (когда нужно выполнить один конкретный цикл)
# replace_message - если не 0, удаляет сообщение перед отправкой нового
async def get_data_cycle(user_id, cycle, user=False, replace_message=0):

    print(f'Читаю файл цикла {cycle} для пользователя {user_id}…')

    if user == False:
        # Путь к файлу данных пользователя
        user_file_path = os.path.join(users_dir, f'{user_id}.json')

        with open(user_file_path, 'r', encoding='utf-8') as f:
            print(f'→ Нашёл профиль', user_file_path)
            user = json.load(f)
            user['user_id'] = user_id

    system_message_id = False
    
    if cycle in user['cycles']:
        subscribe_cycle_button = telebot.types.InlineKeyboardButton(text='⛔️ Отписаться', callback_data=f'unsubscribe_cycle_{cycle}') # Кнопка Отписаться
    else:
        subscribe_cycle_button = telebot.types.InlineKeyboardButton(text='Подписаться на обновления сервиса', callback_data=f'subscribe_cycle_{cycle}') # Кнопка Подписаться
    return_cycles_button = telebot.types.InlineKeyboardButton(text='Список циклов', callback_data='cycles') # Кнопка возврата в меню циклов

    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(subscribe_cycle_button)
    keyboard.add(return_cycles_button)
    #keyboard.add(return_button)

    message = await cycle_manager.start(user, cycle)

    if replace_message == 0:

        if 'media_path' in message:
            with open(message['media_path'], 'rb') as photo:
                # Отправляем изображение с подписью (caption) и кнопками (reply_markup)
                message = await bot.send_photo(user_id, photo, caption=escape_markdown(message['text']), reply_markup=keyboard, parse_mode='MarkdownV2')
        
        else:
            message = await bot.send_message(user_id, escape_markdown(message), reply_markup=keyboard, parse_mode='MarkdownV2')
        
        system_message_id = message.message_id

    else:
        
        await bot.delete_message(user_id, replace_message)
        if 'media_path' in message:
            with open(message['media_path'], 'rb') as photo:
                # Отправляем изображение с подписью (caption) и кнопками (reply_markup)
                message = await bot.send_photo(user_id, photo, caption=escape_markdown(message['text']), reply_markup=keyboard, parse_mode='MarkdownV2')

        else:
            message = await bot.send_message(user_id, escape_markdown(message), reply_markup=keyboard, parse_mode='MarkdownV2')
        
        system_message_id = message.message_id

    if system_message_id != False:
        return system_message_id
    else:
        return False

#
# Для работы с циклами
class CycleManager:
    def __init__(self):
        self.expected_cycle = None

    async def start(self, user, cycle):

        print(f"Запускаю выполнение цикла {cycle} для пользователя {user['user_id']}…")

        user_time = await get_local_time(user['timezone']) # получает локальное время пользователя

        # Путь к файлу цикла
        cycle_file_path = os.path.join(cycles_dir, f'{cycle}.json')

        with open(cycle_file_path, 'r', encoding='utf-8') as f:
            print(f'→ Нашёл цикл', cycle_file_path)
            cycle = json.load(f)

        if cycle['trigger'] == 'time':

            print('Начинаю выполнение цикла по триггеру time…')

            # Извлечение часов из объекта datetime
            current_hour = user_time.hour

            # Исключаем нечисловые ключи
            hours = [int(hour) for hour in cycle.keys() if hour.isdigit()]
            #hours.sort()

            # Создаем диапазоны часов
            hour_ranges = list(zip(hours, hours[1:] + hours[:1]))

            # Находим текущий диапазон часов
            current_range = None
            for start, end in hour_ranges:
                if start <= current_hour < end:
                    current_range = (start, end)
                    break

            # Если диапазон не найден, значит текущий час находится в промежутке между последним и первым часом
            if current_range is None:
                current_range = (hours[-1], hours[0])

            # Если диапазон найден, получить соответствующее значение из данных
            if current_range:
                for index, hour in enumerate(hours):
                    if hour == current_range[0]:
                        return cycle[str(hour)]  # Получить значение по индексу из словаря cycle

        elif cycle['trigger'] == 'sunrise_sunset':

            print('Начинаю выполнение цикла по триггеру sunrise_sunset…')

            # Получение ответов для вчера, сегодня и завтра и сохранение их в отдельные переменные
            response_yesterday, response_today, response_tomorrow = (
                await get_sunrise_sunset(user, user_time - timedelta(days=1)),
                await get_sunrise_sunset(user, user_time),
                await get_sunrise_sunset(user, user_time + timedelta(days=1))
            )

            yesterday_sunset = datetime.strptime(response_yesterday['results']['sunset'], "%Y-%m-%dT%H:%M:%S%z")
            sunrise = datetime.strptime(response_today['results']['sunrise'], "%Y-%m-%dT%H:%M:%S%z")
            sunset = datetime.strptime(response_today['results']['sunset'], "%Y-%m-%dT%H:%M:%S%z")
            tomorrow_sunrise = datetime.strptime(response_tomorrow['results']['sunrise'], "%Y-%m-%dT%H:%M:%S%z")

            text_of_response = ''
            if user_time < sunrise or user_time > sunset:
                if user_time < sunrise:
                    duration = sunrise - yesterday_sunset
                    hour_duration = duration / 12
                    relevant_time = user_time - yesterday_sunset
                    current_hour = int(relevant_time / hour_duration)
                    start = yesterday_sunset + hour_duration * current_hour
                    end = start + hour_duration
                else:
                    duration: timedelta = tomorrow_sunrise - sunset
                    hour_duration = duration / 12
                    relevant_time = user_time - sunset
                    current_hour = int(relevant_time / hour_duration)
                    start = sunset + hour_duration * current_hour
                    end = start + hour_duration
                text_of_response += f'{start.hour}:{start.minute} - {end.hour}:{end.minute}\n'
                text_of_response += f"Сейчас {current_hour} ночной планетарный час\n"
                text_of_response += cycle['night'][str(current_hour - 1)]
                return text_of_response
            else:
                duration: timedelta = sunset - sunrise
                hour_duration = duration / 12
                relevant_time = user_time - sunrise
                current_hour = int(relevant_time / hour_duration)
                start = sunrise + hour_duration * current_hour
                end = start + hour_duration
                text_of_response += f'{start.hour}:{start.minute if start.minute >= 10 else "0" + start.minute.__str__()} - {end.hour}:{end.minute if end.minute >= 10 else "0" + end.minute.__str__()}\n'
                text_of_response += f"Сейчас {current_hour} дневной планетарный час\n"
                text_of_response += cycle['day'][str(current_hour - 1)]
                return text_of_response

        elif cycle['trigger'] == 'date':

            print('Начинаю выполнение цикла по триггеру date…')

            # Получаем текущую дату в формате "день/месяц"
            current_date = user_time.strftime('%d/%m')

            # Создаем список ключей словаря в формате "день/месяц"
            day_month_keys = [key for key in cycle.keys() if '/' in key]

            # Перебираем отсортированные ключи и находим текущий промежуток дат
            current_range_data = None
            for i in range(len(day_month_keys)):
                current_key = day_month_keys[i]
                next_key = day_month_keys[(i + 1) % len(day_month_keys)]
                if current_key <= current_date < next_key:
                    current_range_data = cycle[current_key]
                    break

            if current_range_data is None:
                # Если не найден промежуток, значит, текущая дата попадает в промежуток
                # между последним ключом и первым ключом (переход через конец года)
                current_range_data = cycle[day_month_keys[-1]]

            return current_range_data

        elif cycle['trigger'] == 'exact_day':

            print('Начинаю выполнение цикла по триггеру exact_day…')

            # Извлечение даты из объекта datetime
            current_date = user_time.strftime('%d/%m/%Y')
            current_date_object = datetime.strptime(current_date, "%d/%m/%Y").date()

            date_keys = [key for key in cycle.keys() if re.match(r"\d{2}/\d{2}/\d{4}", key)]
            #date_keys.sort()

            next_date = None
            for date_key in date_keys:
                date_object = datetime.strptime(date_key, "%d/%m/%Y").date()
                if date_object > current_date_object:
                    if next_date is None or date_object < datetime.strptime(next_date, "%d/%m/%Y").date():
                        next_date = date_key

            if next_date is not None:
                # Это здесь потому что в словаре циклов могут быть дополнительные параметры для даты
                if 'text' in cycle[next_date]:
                    return cycle[next_date]['text']
                else:
                    return cycle[next_date]
                
            else:
                return 'У меня пока нет даты следующего цикла, попробуй проверить позже…'
        
        elif cycle['trigger'] == 'exact_day_and_time':

            print('Начинаю выполнение цикла по триггеру exact_day_and_time...')
            
            # Текущая дата и время из объекта datetime
            current_datetime = user_time.replace(tzinfo=None)

            # Извлечение всех ключей, которые представляют дату и время
            datetime_keys = [key for key in cycle.keys() if re.match(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}", key)]
            #datetime_keys.sort()

            next_datetime = None
            for datetime_key in datetime_keys:
                datetime_object = datetime.strptime(datetime_key, "%d/%m/%Y %H:%M")
                # Если дата и время из словаря больше текущей даты и времени и либо это первая найденная дата, либо она ближе к текущей
                if datetime_object > current_datetime and (next_datetime is None or datetime_object < next_datetime):
                    next_datetime = datetime_object

            if next_datetime:
                next_datetime_str = next_datetime.strftime("%d/%m/%Y %H:%M")
                # Проверяем, есть ли дополнительный текст для этой даты и времени
                if next_datetime_str in cycle:
                    return cycle[next_datetime_str]
                else:
                    return 'Действие для этой даты и времени не определено.'
            else:
                return 'У меня пока нет данных о следующем событии. Попробуйте проверить позже.'

        elif cycle['trigger'] == 'week_day':

            print('Начинаю выполнение цикла по триггеру week_day…')

            english_to_russian_days = {
                "Monday": "Понедельник",
                "Tuesday": "Вторник",
                "Wednesday": "Среда",
                "Thursday": "Четверг",
                "Friday": "Пятница",
                "Saturday": "Суббота",
                "Sunday": "Воскресенье"
            }

            current_week_day = user_time.strftime('%A')

            return f'**{english_to_russian_days[current_week_day]}**\n\n{cycle[current_week_day]}'

        elif cycle['trigger'] == 'year_periodic':

            print('Начинаю выполнение цикла по триггеру year_periodic…')

            # Текущая дата
            current_date = datetime.strptime(user_time.strftime('%d.%m.%Y'), "%d.%m.%Y").date()

            # Дата рождения пользователя
            birth_date = datetime.strptime(user['birth_day'], '%d.%m.%Y').date()

            # Рассчитываем текущий возраст пользователя
            current_age = current_date.year - birth_date.year

            # Находим ближайший возраст из словаря
            nearest_age = min(int(age) for age in cycle.keys() if age.isdigit() and int(age) >= current_age)

            # Рассчитываем дату следующего дня рождения с найденным возрастом
            next_birthday = birth_date.replace(year=birth_date.year + nearest_age)

            # Если день рождения уже прошел в этом году, переходим к следующему году
            if next_birthday < current_date:
                next_birthday = next_birthday.replace(year=next_birthday.year + 1)

            # Рассчитываем количество дней до следующего дня рождения
            days_until_next_birthday = (next_birthday - current_date).days

            # Рассчитываем количество лет, месяцев, недель и дней
            years = days_until_next_birthday // 365
            remaining_days = days_until_next_birthday % 365
            months = remaining_days // 30
            remaining_days %= 30
            weeks = remaining_days // 7
            remaining_days %= 7

            # Формируем строку с подробной информацией о времени до дня рождения
            time_until_next_birthday = ""
            if years:
                time_until_next_birthday += f"{years} лет, "
            if months:
                time_until_next_birthday += f"{months} месяцев, "
            if weeks:
                time_until_next_birthday += f"{weeks} недель, "
            if remaining_days:
                time_until_next_birthday += f"{remaining_days} дней"
            # Убираем лишнюю запятую и пробел в конце строки
            time_until_next_birthday = time_until_next_birthday.rstrip(", ")

            # Возвращаем строку с информацией о цикле и времени до следующего дня рождения
            return f"{cycle['info']}\n\nДо следующего цикла: {time_until_next_birthday}"

        elif cycle['trigger'] == 'live_biorythms':

            print('Начинаю выполнение цикла по триггеру live_biorythms…')

            # Извлечение даты из объекта datetime
            current_date = user_time.strftime('%d.%m.%Y')
            current_date_object = datetime.strptime(current_date, "%d.%m.%Y").date()

            def p_rhytm(x):
                return math.sin((2 * math.pi * x) / 23)

            def e_rhytm(x):
                return math.sin((2 * math.pi * x) / 28)

            def i_rhytm(x):
                return math.sin((2 * math.pi * x) / 33)

            _range = 10

            start_date = current_date_object - timedelta(days=_range)

            diff = start_date - datetime.strptime(user['birth_day'], "%d.%m.%Y").date()
            _days = diff.total_seconds() // 86400

            p_rhytms = []
            e_rhytms = []
            i_rhytms = []
            nums = []
            days = []

            for i in range(_range * 2):
                days.append(_days)

                p_rhytms.append(p_rhytm(_days))
                e_rhytms.append(e_rhytm(_days))
                i_rhytms.append(i_rhytm(_days))

                _days += 1

                nums.append(start_date.day)

                start_date += timedelta(days=1)

            fig = plt.figure()
            ax = fig.add_subplot()

            ax.yaxis.set_major_locator(ticker.FixedLocator([0]))
            ax.yaxis.set_major_formatter(ticker.FixedFormatter(['Медиана']))

            ax.xaxis.set_major_locator(ticker.FixedLocator(days))
            ax.xaxis.set_major_formatter(ticker.FixedFormatter(nums))

            ax.grid(True, axis='both')
            ax.set_xlabel('Дни', loc='center')

            ax.plot(days, p_rhytms, 'r', label='Физический ритм')
            ax.plot(days, e_rhytms, 'g', label='Эмоциональный ритм')
            ax.plot(days, i_rhytms, 'b', label='Интеллектуальный ритм')

            ax.legend(loc='lower right')

            media_path = f"/tmp/live_biorythms_{user['user_id']}.png"
            fig.savefig(media_path)

            result = {'text': 'Биоритмы человека', 'media_path': media_path}
            return result

        elif cycle['trigger'] == 'blood_moon':

            print('Начинаю выполнение цикла по триггеру blood_moon…')

            birth_date = datetime.strptime(user['birth_day'], "%d.%m.%Y").date()

            # Извлечение даты из объекта datetime
            current_date = datetime.strptime(user_time.strftime('%d.%m.%Y'), "%d.%m.%Y").date()
            start_date = current_date - timedelta(days=10)

            diff = start_date - birth_date
            num_days = diff.days  # Исправление ошибки

            p_rhythms = []
            e_rhythms = []
            i_rhythms = []
            b_rhythms = []
            nums = []
            days = []

            for i in range(20):
                days.append(num_days)

                p_rhythms.append(math.sin((2 * math.pi * num_days) / 23))
                e_rhythms.append(math.sin((2 * math.pi * num_days) / 28))
                i_rhythms.append(math.sin((2 * math.pi * num_days) / 33))
                b_rhythms.append(math.sin((2 * math.pi * num_days) / 28) + math.sin((2 * math.pi * num_days) / 33))

                num_days += 1

                nums.append(start_date.day)

                start_date += timedelta(days=1)

            fig, ax = plt.subplots()

            ax.yaxis.set_major_locator(ticker.FixedLocator([0]))
            ax.yaxis.set_major_formatter(ticker.FixedFormatter(['Медиана']))

            ax.xaxis.set_major_locator(ticker.FixedLocator(days))
            ax.xaxis.set_major_formatter(ticker.FixedFormatter(nums))

            ax.grid(True, axis='both')
            ax.set_xlabel('Дни', loc='center')

            ax.plot(days, p_rhythms, label='Физический')
            ax.plot(days, e_rhythms, label='Эмоциональный')
            ax.plot(days, i_rhythms, label='Интеллектуальный')
            ax.plot(days, b_rhythms, label='По крови')

            ax.legend(loc='upper left')
            # ax.set_xlabel('Дни')
            # ax.set_ylabel('Значения')

            plt.title('График биоритмов и цикла крови по Луне')
            # plt.show()
            media_path = f"/tmp/blood_moon_{user['user_id']}.png"
            fig.savefig(media_path)

            result = {'text': 'Цикл крови по Луне', 'media_path': media_path}
            return result

        elif cycle['trigger'] == 'periods_make_money':

            print('Начинаю выполнение цикла по триггеру periods_make_money…')

            date = datetime.strptime(user_time.strftime('%d.%m.%Y'), "%d.%m.%Y").date()

            now = datetime.now()
            end_year = int(now.year) + 90

            # Алгоритм считает годы Тяжёлых времён по циклу Беннера
            sequence = [7, 11, 9]
            years = []
            start_year = 1924
            index = (start_year - 1924) % len(sequence)
            while start_year <= end_year:
                years.append(start_year)
                start_year += sequence[index]
                index = (index + 1) % len(sequence)
            bad_years = years[-16:]

            # Алгоритм считает годы Хороших времён по циклу Беннера
            sequence = [8, 9, 10]
            years = []
            start_year = 1918
            index = (start_year - 1918) % len(sequence)
            while start_year <= end_year:
                years.append(start_year)
                start_year += sequence[index]
                index = (index + 1) % len(sequence)
            good_years = years[-15:]

            # Алгоритм считает годы Паники по циклу Беннера
            sequence = [18, 20, 16]
            years = []
            start_year = 1873
            index = (start_year - 1873) % len(sequence)
            while start_year <= end_year:
                years.append(start_year)
                start_year += sequence[index]
                index = (index + 1) % len(sequence)
            panic_years = years[-8:]

            # Создание графика
            fig, ax = plt.subplots(figsize=(12, 6))

            # Установка шкалы времени по оси X
            ax.set_xticks(bad_years + panic_years + good_years)
            ax.set_xticklabels([''] * len(bad_years + panic_years + good_years))

            # Создание второго графика
            all_years = sorted(bad_years + panic_years + good_years)
            good_points = [(year, 1.5) for year in good_years]
            ax.plot([point[0] for point in good_points], [point[1] for point in good_points], 'b')

            # Соединение точек линиями
            all_points = sorted([(year, 1) for year in bad_years] + [(year, 2) for year in panic_years] + good_points)
            ax.plot([point[0] for point in all_points], [point[1] for point in all_points], 'b')

            # Добавление линии между нижними точками пирамидок
            bad_last_point = (bad_years[-1], 1)
            panic_last_point = (panic_years[-1], 2)
            if bad_last_point == panic_last_point:
                ax.plot([bad_last_point[0], panic_last_point[0]], [bad_last_point[1], panic_last_point[1]], 'r')

            # Отображение годов около точек на графике
            for year in bad_years:
                ax.text(year, 0.97, str(year), ha='center', va='bottom')

            for year in panic_years:
                ax.text(year, 2, str(year), ha='center', va='bottom')

            for year in good_years:
                ax.text(year, 1.5, str(year), ha='center', va='bottom')

            # Проверка совпадения второго графика с первым
            if all_points[-1] == good_points[-1]:
                ax.plot([all_points[-1][0], good_points[-1][0]], [all_points[-1][1], good_points[-1][1]], 'b')

            # Установка обозначений на оси Y
            ax.set_yticks([1, 1.5, 2])
            ax.set_yticklabels(['C', 'B', 'A'])

            media_path = f"/tmp/periods_mm_{user['user_id']}.png"
            # Сохранение графика в виде изображения
            fig.savefig(media_path)
            plt.close(fig)  # Закрытие графика

            result = {'text': 'Благоприятное время для сделок', 'media_path': media_path}
            return result

        elif cycle['trigger'] == 'random':
            print('Начинаю выполнение цикла по триггеру random…')
            random_number = random.randint(0, 64)
            response_text = "Случайное сообщение " + str(random_number)
            return response_text

        else:
            print('Начинаю выполнение цикла по другому триггеру… (example)')
            return "Сезон\nМесяц\nОрган\nМеридиан\nФокус внимания"
#
# Для работы с файлом профиля и валидации входных данных
class ProfileEditor:
    def __init__(self):
        self.expected_field = None
        self.param_labels = {
            'full_name': 'Полное имя (ФИО)',
            'birth_day': 'Дата рождения (ДД.ММ.ГГГГ)',
            'birth_time': 'Время рождения (ЧЧ:ММ)',
            'timezone': 'Часовой пояс (GMT±N)',
            'location': 'Местоположение (Широта,Долгота)',
            'birth_place': 'Место рождения'
        }
        self.param_formats = {
            'full_name': r'^[\w\s]+$',
            'birth_day': r'^\d{2}\.\d{2}\.\d{4}$',
            'birth_time': r'^\d{2}:\d{2}$',
            'timezone': r'^GMT[+-]\d+$',
            'location': r'\s*(\-?\d+\.\d+),?\s*(\-?\d+\.\d+)\s*',
            'birth_place': r'^[\w\s]+$'
        }

    def start_editing(self, user_id, profile_param):
        # Устанавливаем ожидаемый параметр для ввода
        if profile_param in self.param_labels:
            self.expected_field = profile_param
            label = self.param_labels[profile_param]
            if profile_param == 'timezone':
                print(f'Ожидаю ввода {label} от пользователя {user_id}…')
                return f"Введите {label} или нажмите соответствующую кнопку"
            elif profile_param == 'location':
                print(f'Ожидаю ввода {label} от пользователя {user_id}…')
                return f"Введите {label} в формате (Широта,Долгота)"
            else:
                print(f'Ожидаю ввода {label} от пользователя {user_id}…')
                return f"Введите {label}"
        else:
            print(f'x Пользователь {user_id} попытался обновить неизвестный параметр профиля!')
            return "❗️Неверный параметр профиля."

    def process_input(self, user_id, input_data):
        if self.expected_field:
            # Обработка ввода
            profile_param = self.expected_field
            # Проверка соответствия введенных данных формату параметра профиля
            if profile_param == 'location':
                
                # Проверка формата для координат
                if not re.match(self.param_formats['location'], input_data):
                    print(f'Пользователь {user_id} ввёл некорректные координаты!')
                    return f"❗️Введенные данные для широты и долготы не соответствуют формату. Пожалуйста, введите данные в правильном формате (Широта,Долгота)."
                
                # Если данные предоставлены через message.location
                if isinstance(input_data, dict):
                    latitude = input_data['latitude']
                    longitude = input_data['longitude']
                else:
                    # Если формат координат верный, разделите их и обработайте отдельно
                    latitude, longitude = map(float, input_data.split(','))

                user_file_path = os.path.join(users_dir, f'{user_id}.json')
                
                if os.path.exists(user_file_path):
                    with open(user_file_path, 'r', encoding='utf-8') as f:
                        profile = json.load(f)
                else:
                    profile = {}
                
                profile['latitude'] = latitude
                profile['longitude'] = longitude
                
                with open(user_file_path, 'w', encoding='utf-8') as f:
                    json.dump(profile, f, ensure_ascii=False)
                self.expected_field = None
                print(f'Пользователь {user_id} обновил координаты своего местонахождения!')
                
                return "Профиль обновлён:\n\n✅ Местоположение"
            elif not re.match(self.param_formats[profile_param], input_data):
                label = self.param_labels[profile_param]
                print(f'Пользователь {user_id} ввёл некорректные данные для {label}!')
                return f"❗️Введенные данные не соответствуют формату {label}. Пожалуйста, введите данные в правильном формате."
            else:
                label = self.param_labels[profile_param]
                # Записываем введенную информацию в файл профиля пользователя
                user_file_path = os.path.join(users_dir, f'{user_id}.json')
                if os.path.exists(user_file_path):
                    with open(user_file_path, 'r', encoding='utf-8') as f:
                        profile = json.load(f)
                else:
                    profile = {}
                profile[profile_param] = input_data
                with open(user_file_path, 'w', encoding='utf-8') as f:
                    json.dump(profile, f, ensure_ascii=False)
                
                self.expected_field = None
                print(f'Пользователь {user_id} обновил {label}!')
                return f"Профиль обновлён:\n\n✅ {self.param_labels[profile_param]}"
        else:
            if input_data.startswith('cycle_'):

                user_file_path = os.path.join(users_dir, f'{user_id}.json')
                action = input_data[len("cycle_"):]

                # Читаем содержимое файла профиля
                with open(user_file_path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)

                if action.startswith('add_'):
                    cycle = action[len("add_"):]
                    profile['cycles'].append(cycle)
                elif action.startswith('remove_'):
                    cycle = action[len("remove_"):]
                    profile['cycles'].remove(cycle)

                # Записываем обновленные данные обратно в файл профиля
                with open(user_file_path, 'w', encoding='utf-8') as f:
                    json.dump(profile, f, ensure_ascii=False)

                print(f'Пользователь {user_id} обновил свой список подписок на циклы')

            elif input_data.startswith('ref_'):

                user_file_path = os.path.join(users_dir, f'{user_id}.json')
                referal = input_data[len("ref_add_"):]

                # Читаем содержимое файла профиля
                with open(user_file_path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)

                profile['referals'].append(referal)

                # Записываем обновленные данные обратно в файл профиля
                with open(user_file_path, 'w', encoding='utf-8') as f:
                    json.dump(profile, f, ensure_ascii=False)

                print(f'У пользователя {user_id} обновился список рефералов')

            else:
                return "Нет ожидаемого параметра для ввода."


try:
    # Открываем файл для чтения
    with open('token', 'r') as file:
        # Читаем содержимое файла
        lines = file.readlines()

        # Проходим по каждой строке файла
        for line in lines:
            # Разделяем строку по символу '='
            parts = line.split('=')
            # Если нашли строку с переменной TOKEN
            if len(parts) == 2 and parts[0].strip() == 'TOKEN':
                # Извлекаем значение токена
                token = parts[1].strip()
                print("Токен бота загружен.")
                # Можно использовать токен здесь
                TOKEN = token
                break
            else:
                print("\n\nПроверь правильность своего токена в файле bot/token, должно быть так TOKEN = 'YOUR_TOKEN'")
                # Завершаем выполнение программы
                sys.exit()
except FileNotFoundError as e:
    print("\n\nСоздай файл token в папке с ботом 'bot/' и пропиши туда свой токен TOKEN = 'YOUR_TOKEN'\nОбрати внимание, рабочая директория для запуска бота должна соответствовать ../bot")
    # Завершаем выполнение программы
    sys.exit()
except Exception as e:
    # Обработка других исключений
    print("\n\nПроизошла ошибка:", e)
    sys.exit()

# Создаем экземпляр бота
bot = AsyncTeleBot(TOKEN)
# bot = telebot.TeleBot(TOKEN)
profile_editor = ProfileEditor()
cycle_manager = CycleManager()

cycles = scan_cycles()


# Обработчик команды /start
@bot.message_handler(commands=['start'])
async def start(message):
    user_id = message.chat.id
    start_param = message.text.split(' ')[-1]

    # Отправляем приветственное сообщение
    if start_param:
        await create_or_load_user_data(user_id, start_param)
    else:
        await create_or_load_user_data(user_id)

    update_week_activity_data()

    #bot.send_message(message.chat.id, "Вот мои циклы:")
    #bot.send_message(message.chat.id, '\n'.join(cycles))


# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
async def handle_message(message):
    user_id = message.from_user.id
    # Создание inline клавиатуры кнопок для меню
    keyboard = telebot.types.InlineKeyboardMarkup()

    if profile_editor.expected_field:
        # Бот ожидает ввода данных профиля
        response = profile_editor.process_input(user_id, message.text)
        keyboard.add(return_button_disallow_delete_msg)
        await bot.reply_to(message, response, reply_markup=keyboard)

        if system_message_ids.get(user_id):
            await bot.delete_message(user_id, system_message_ids[user_id])
            system_message_ids[user_id] = False

        system_message_ids[user_id] = await get_update_profile(user_id)
    else:
        # Бот не ожидает ввода данных профиля
        #print(message)
        print(f'Пользователь {user_id} написал: {message.text}')

    update_week_activity_data()


# Обработчик сообщений с геолокацией,
# он сделает тоже что и при ручном вводе геолокации,
# просто петухон любит использовать кучу обработчиков!
@bot.message_handler(content_types=['location'])
async def handle_location(message):
    user_id = message.from_user.id
    # Создание inline клавиатуры кнопок для меню
    keyboard = telebot.types.InlineKeyboardMarkup()

    input_data = f'{message.location.latitude},{message.location.longitude}'

    if profile_editor.expected_field:
        # Бот ожидает ввода данных профиля
        response = profile_editor.process_input(user_id, input_data)
        keyboard.add(return_button_disallow_delete_msg)
        await bot.reply_to(message, response, reply_markup=keyboard)

        if system_message_ids.get(user_id):
            await bot.delete_message(user_id, system_message_ids[user_id])
            system_message_ids[user_id] = False

        system_message_ids[user_id] = await get_update_profile(user_id)
    else:
        # Бот не ожидает ввода данных профиля
        #print(message)
        print(f'Пользователь {user_id} прислал геолокацию, я не ждал от него такого: {message.location}')

    update_week_activity_data()


@bot.callback_query_handler(func=lambda call: True)
async def handle_callback_query(call):
    user_id = call.from_user.id
    message_id = call.message.message_id
    # здесь вы можете обрабатывать callback_query
    # например, извлекать данные из call.data и реагировать соответствующим образом


    #
    # Кнопки для циклов:
    #
    # Проверка, начинается ли текст кнопки с "cycle_"
    if call.data.startswith("cycle_"):
        # Извлечение значения после "set_"
        param_name = call.data[len("cycle_"):]

        # Вызов функции some_func с параметром param_name
        system_message_ids[user_id] = await get_data_cycle(user_id, cycle=param_name, replace_message=message_id)
        await bot.answer_callback_query(call.id)

    #
    # Кнопки Главное меню
    #
    elif call.data == 'main_menu':
        await send_menu(user_id, 'hello', message_id)
        await bot.answer_callback_query(call.id) # убирает анимацию загрузки кнопки
        profile_editor.expected_field = None # сбрасывает состояние ожидания ввода от пользователя
    elif call.data == 'main_menu_for_not_delete_msg':
        await send_menu(user_id, 'hello')
        await bot.answer_callback_query(call.id) # убирает анимацию загрузки кнопки
        profile_editor.expected_field = None # сбрасывает состояние ожидания ввода от пользователя


    #
    # Кнопка Заполнить профиль
    #
    elif call.data == 'completed_profile':
        system_message_ids[user_id] = await get_update_profile(user_id)
        await bot.answer_callback_query(call.id)


    #
    # Кнопки для главного меню:
    # Циклы, Настройки и пр.
    #
    elif call.data == 'compatibility':
        await send_menu(user_id, 'compatibility', message_id)
        await bot.answer_callback_query(call.id)
    elif call.data == 'cycles':
        await send_menu(user_id, 'cycles', message_id)
        await bot.answer_callback_query(call.id)
    elif call.data == 'settings':
        await send_menu(user_id, 'settings', message_id)
        await bot.answer_callback_query(call.id)
    elif call.data == 'ads':
        await send_menu(user_id, 'ads', message_id)
        await bot.answer_callback_query(call.id)
    elif call.data == 'contacts':
        await send_menu(user_id, 'contacts', message_id)
        await bot.answer_callback_query(call.id)
    elif call.data == 'subscription':
        await send_menu(user_id, 'subscription', message_id)
        await bot.answer_callback_query(call.id)
    elif call.data == 'referal_get_link':
        await send_menu(user_id, 'referal_get_link', message_id)
        await bot.answer_callback_query(call.id)
    elif call.data == 'prognostics':
        await send_menu(user_id, 'prognostics', message_id)
        await bot.answer_callback_query(call.id)

    #
    # Кнопки управления партнёрами в сервисе совместимости
    #
    elif call.data == 'partner_add':
        await send_menu(user_id, 'partner_add', message_id)
        await bot.answer_callback_query(call.id)
    # Проверка, начинается ли текст кнопки с "partner_"
    elif call.data.startswith("partner_"):
        # Извлечение значения после "partner_"
        param_name = call.data[len("partner_"):]
        option_data = await get_partner(user_id, target=param_name)

        # Вызов функции some_func с параметром param_name
        await send_menu(user_id, 'partner_show', message_id, option_data)
        await bot.answer_callback_query(call.id)

    #
    # Кнопки для категорий циклов
    # Личные, Сегодня, Будущее и др.
    #
    elif call.data == 'cycles_personal':
        await send_menu(user_id, 'cycles_personal', message_id)
        await bot.answer_callback_query(call.id)
    elif call.data == 'cycles_investment':
        await send_menu(user_id, 'cycles_investment', message_id)
        await bot.answer_callback_query(call.id)
    elif call.data == 'cycles_sun':
        await send_menu(user_id, 'cycles_sun', message_id)
        await bot.answer_callback_query(call.id)
    elif call.data == 'cycles_retrogrades':
        await send_menu(user_id, 'cycles_retrogrades', message_id)
        await bot.answer_callback_query(call.id)

    #
    # Кнопка получения информации о сегодняшних циклах (на которые подписан пользователь)
    #
    elif call.data == 'get_active_cycles':
        await send_menu(user_id, 'get_active_cycles', message_id)
        await bot.answer_callback_query(call.id)

    #
    # Кнопки получения информации о циклах из будущего (на которые подписан пользователь)
    # Завтра, На месяц, Планетарные циклы (до 100 лет)
    #
    elif call.data == 'get_active_cycles_next':
        await send_menu(user_id, 'get_active_cycles_next', message_id)
        await bot.answer_callback_query(call.id)
    elif call.data == 'get_active_cycles_next_1':
        await send_menu(user_id, 'get_active_cycles_next_1', message_id)
        await bot.answer_callback_query(call.id)
    elif call.data == 'get_active_cycles_next_30':
        await send_menu(user_id, 'get_active_cycles_next_30', message_id)
        await bot.answer_callback_query(call.id)
    elif call.data == 'get_active_cycles_next_100':
        await send_menu(user_id, 'get_active_cycles_next_100', message_id)
        await bot.answer_callback_query(call.id)

    #
    # Кнопка получения информации о текущей подписке пользователя
    #
    elif call.data == 'my_subscription_info':
        await send_menu(user_id, 'my_subscription_info', message_id)
        await bot.answer_callback_query(call.id)

    #
    # Кнопки для настроек:
    # Имя, Местоположение и пр.
    #
    # Проверка, начинается ли текст кнопки с "set_"
    elif call.data.startswith("set_"):
        # Извлечение значения после "set_"
        param_name = call.data[len("set_"):]

        # Вызов функции some_func с параметром param_name
        message = await get_update_profile(user_id, field=param_name, replace_message=message_id)
        system_message_ids[user_id] = message
        await bot.answer_callback_query(call.id)

    #
    # Кнопки подписаться на цикл
    #
    # Проверка, начинается ли текст кнопки с "subscribe_cycle_"
    elif call.data.startswith("subscribe_cycle_"):
        # Извлечение значения после "set_"
        param_name = call.data[len("subscribe_cycle_"):]

        await bot.answer_callback_query(call.id, text=f"✅ Ты успешно подписался на обновления {param_name}")

        await get_update_profile(user_id, field=f'cycle_{param_name}')
        await get_data_cycle(user_id, cycle=param_name, replace_message=message_id)

        # Вызов функции some_func с параметром param_name
        print(f'Пользователь {user_id} подписался на обновления {param_name}')

    #
    # Кнопки отписаться от цикла
    #
    # Проверка, начинается ли текст кнопки с "unsubscribe_cycle_"
    elif call.data.startswith("unsubscribe_cycle_"):
        # Извлечение значения после "set_"
        param_name = call.data[len("unsubscribe_cycle_"):]

        await bot.answer_callback_query(call.id, text=f"⛔️ Ты успешно отписался от обновлений {param_name}")

        await get_update_profile(user_id, field=f'cycle_{param_name}')
        await get_data_cycle(user_id, cycle = param_name, replace_message = message_id)

        # Вызов функции some_func с параметром param_name
        print(f'Пользователь {user_id} отписался от обновлений {param_name}')

    update_week_activity_data()
    print(f"Пользователь {user_id} нажал на кнопку: {call.data}")


import asyncio
# Запускаем бота
asyncio.run(bot.polling())
