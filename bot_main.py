# -*- coding: utf-8 -*-
# import logging
import time

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from config import TOKEN, CHAT_ID, ALL_USERS, USERS_ADM
import keyboards as kb
# import ah_main as main
import asyncio
# import aioschedule
import aiogram
import bot_functions as bot_f
import bot_logging as logbot
import subprocess
import funcs_for_ok as ok_f
import os


bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())



class OkState(StatesGroup):
    OkSt = State()


class BotDialog_number(StatesGroup):
    mess_state_number = State()
    mess_state_discription = State()


class BotDialog_ban(StatesGroup):
    ban_number_state = State()
    ban_days_state = State()
    ban_discription_state = State()

class BotDialog_queues(StatesGroup):
    queue_show_state = State()
    queue_member_remove_state = State()
    queue_discription_state = State()

class BotDialog_records(StatesGroup):
    records_state = State()

class BotDialog_cancel(StatesGroup):
    mess_state_1 = State()
    mess_state_2 = State()


@dp.message_handler(commands=['start'])
async def process_start(message: types.Message):
    if bot_f.check_permissions(message.from_user.id):
        await bot.send_message(message.chat.id,
                               f'Добро пожаловать, {message.chat.username}',
                               reply_markup=kb.greet_kb_hi)
    else:
        await bot.send_message(message.chat.id, 'У вас нету доступа к боту. Обратитесь в Тех. поддержку')


@dp.message_handler(text=['Начать работу'])
async def process_start1(message: types.Message):
    await bot.send_message(message.chat.id,
                           'Выберите команду',
                           reply_markup=kb.greet_kb_main)
    logbot.log_info(f'Пользователь {message.chat.username} нажал кнопку {message.text}')


@dp.message_handler(text=['Вернуться ко всем командам'])
async def process_back(message: types.Message):
    await bot.send_message(message.chat.id,
                           'Выберите команду',
                           reply_markup=kb.greet_kb_main)


@dp.message_handler(text=['Раскрытие номера'])
async def process_number(message: types.Message):
    if bot_f.check_permissions(message.from_user.id):
        await BotDialog_number.mess_state_number.set()
        # await message.reply(message.from_user.id, reply=False)
        await bot.send_message(message.chat.id,
                               'Введите последние 5 цифр номера и через пробел причину раскрытия',
                               reply_markup=kb.greet_kb_back)
    else:
        await bot.send_message(message.chat.id,
                               'У вас нету доступа. Обратитесь в Тех. поддержку')


@dp.message_handler(state=BotDialog_number.mess_state_number)
async def process_number_answer(message: types.Message, state: FSMContext):
    async with state.proxy() as data:  # Устанавливаем состояние ожидания
        data['get_number'] = ''  # Создание пустого значения с ключом get_number
        data['back_number'] = ''  # Создание пустого значения с ключом back_number для возврата
        data['description'] = ''  # Создание пустого значения с ключом description для описания
        # xx = message.text.split(' ', 1)
        while data['get_number'] == '' or data['back_number'] == '':
            if message.text == 'Вернуться ко всем командам':
                data['back_number'] = 'Возврат во всем командам'
                await bot.send_message(message.from_user.id,
                                       data['back_number'],
                                       reply_markup=kb.greet_kb_main)
                await state.finish()
                return
            elif bot_f.isint_for_get_number(message.text.split(' ', 1)[0].strip()) != True:
                await message.reply('Пожалуйста, введите последние 5 цифр номера и причину раскрытия')
                return
            elif bot_f.isint_for_get_number(message.text.split(' ', 1)[0].strip()) == True:
                data['get_number'] = message.text.split(' ', 1)[0].strip()
                data['description'] = message.text.split(' ', 1)[1].strip()
                answer_number = bot_f.get_number(data['get_number'])
                await bot.send_message(
                    message.from_user.id,
                    answer_number,
                    reply_markup=kb.greet_kb_main,
                    parse_mode='HTML'
                )
                logbot.log_info(f"Пользователь {message.from_user.username} раскрыл номер "
                                f"{answer_number.split('|')[0].split(':')[1].strip()} "
                                f"с причиной раскрытия \"{data['description']}\"")
                await state.finish()
                return


@dp.message_handler(text=['Добавление номера в BL'], state='*')
async def process_black_list(message: types.Message, state: FSMContext):
    if message.from_user.id in USERS_ADM:
        await bot.send_message(message.chat.id,
                               'Введите последние 5 цифр номера',
                               reply_markup=kb.greet_kb_back)
        await BotDialog_ban.ban_number_state.set()
        logbot.log_info(f"Пользователь {message.from_user.username}({message.from_user.id}) "
                        f"получил доступ на добавление номера в Черный Список")
    else:
        await message.reply("У вас нету доступа", reply=False)
        logbot.log_info(f"Пользователь {message.from_user.username}({message.from_user.id}) "
                        f"попытался получить к команде добавления номера в Черный Список")


@dp.message_handler(state=BotDialog_ban.ban_number_state)
async def process_black_list_find_num(message: types.Message, state: FSMContext):
    if message.text == 'Вернуться ко всем командам':
        await message.reply("Возврат ко всем командам", reply=False, reply_markup=kb.greet_kb_main)
        await state.finish()
    else:
        if not bot_f.isint_for_get_number(message.text.strip()):
            await message.reply("Пожалуйста, введите последние 5 цифр номера", reply=False)
            return
        try:
            numb, calldate = bot_f.get_number_for_BL(message.text.strip())
            await state.update_data(number=numb)
            if numb == None:
                await message.reply("За последние 3 дня не найдено звонков, проверьте правильность ввода", reply=False)
                logbot.log_info(f"Пользователь {message.from_user.username}({message.from_user.id}) "
                                f"попытался найти номер *****{message.text.strip()} для блокировки, "
                                f"но за последние 3 дня не было звонков с этого номера.")
                return
            else:
                await bot.send_message(message.chat.id,
                                       f'Номер 7{numb} последний раз звонил {calldate}.'
                                       f' Если дата не верная, то обратитесь к администратору')
                await bot.send_message(message.chat.id, 'Введите причину бана')
                await BotDialog_ban.ban_discription_state.set()
                logbot.log_info(f"Пользователь {message.from_user.username}({message.from_user.id}) "
                                f"раскрыл номер {numb} для блокировки")
        except:
            await message.reply("За последние 3 дня не найдено звонков, проверьте правильность ввода", reply=False)
            return


@dp.message_handler(state=BotDialog_ban.ban_discription_state)
async def process_black_list_description(message: types.Message, state: FSMContext):
    if message.text == 'Вернуться ко всем командам':
        await message.reply("Возврат ко всем командам", reply=False, reply_markup=kb.greet_kb_main)
        await state.finish()
    else:
        if len(message.text) < 5:
            await message.reply("Пожалуйста, напишите более подробную причину", reply=False)
            logbot.log_info(f"Пользователь {message.from_user.username}({message.from_user.id}) "
                            f"ввел некоректную причину блокировки номера: {message.text}")
            return
        await state.update_data(description=message.text.strip())
        await message.reply("Введите количество дней бана или введите 'Час' для блокировки на час",
                            reply=False, reply_markup=kb.greet_kb_bl)  # , reply_markup=kb.inline_kb1)
        await BotDialog_ban.ban_days_state.set()


@dp.message_handler(state=BotDialog_ban.ban_days_state)
async def process_black_list_dur_and_baned(message: types.Message, state: FSMContext):
    if message.text == 'Вернуться ко всем командам':
        await message.reply("Возврат ко всем командам", reply=False, reply_markup=kb.greet_kb_main)
        await state.finish()
    else:
        if message.text.lower() in ['час', 'забанить на час']:
            await state.update_data(days='час')
        elif message.text.isalpha():
            await message.reply("Пожалуйста, введите количество дней числом или введите 'Час' для блокировки на час",
                                reply=False)
            return
        else:
            await state.update_data(days=message.text.strip())
        data = await state.get_data()
        num, desc, d = data.values()
        ans = f'{d}' if d == 'час' else f'{d} дней'
        try:
            bot_f.ban_number(int(num), desc, d)
            await message.reply(f"Номер 7{num} был забанен на {ans} по причине {desc}", 
                                reply=False, reply_markup=kb.greet_kb_main)
            logbot.log_info(f"Пользователь {message.from_user.username}({message.from_user.id}) "
                            f"забанил номер {num} на {ans} по причине {desc}")
        except:
            await message.reply(f"Номер 7{num} не был забанен. Попробуйте ещё раз или обратитесь к администратору.",
                                reply=False, reply_markup=kb.greet_kb_main)
            logbot.log_error(f"У пользователя {message.from_user.username}({message.from_user.id}) "
                             f"не получилось забанить номер {num} на {ans} по причине {desc}")
        await state.finish()


@dp.message_handler(text=['Выкидывание из очереди добавочного'])
async def process_queue(message: types.Message):
    await bot.send_message(message.chat.id,
                           'Введите добавочный для выкидывания его из очереди',
                           reply_markup=kb.greet_kb_back)
    await BotDialog_queues.queue_show_state.set()
    logbot.log_info(f"Пользователь {message.from_user.username}({message.from_user.id}) "
                    f"получил доступ к удалению из очереди")


@dp.message_handler(state=BotDialog_queues.queue_show_state)
async def process_black_list_dur_and_baned(message: types.Message, state: FSMContext):
    logbot.log_info(f"Пользователь {message.from_user.username}({message.from_user.id}) "
                    f"для удаления из очереди ввёл {message.text}")
    if len(message.text.strip()) == 3 and message.text.strip().isdigit() == True:
        try:
            await bot.send_message(message.chat.id, f'Очереди в которых есть добавочный \n {bot_f.show_queues(message.text.strip())}', reply_markup=kb.greet_yes_no)
            await state.update_data(member=message.text.strip())
            await state.update_data(queues=bot_f.show_queues(message.text.strip()))
            await BotDialog_queues.queue_member_remove_state.set()
        except:
            await bot.send_message(message.chat.id, f'Добавочного {message.text.strip()} нет в очередях или его не существует\nВведите другой добавочный или вернитесь ко всем командам')
    elif message.text.lower() == 'всех':
        if message.from_user.id in USERS_ADM:
            sips = bot_f.show_queues_all()
#        await bot.send_message(message.chat.id, f"{sips}")
            for i in sips:
#            await bot.send_message(message.chat.id, f"Удаление {i}")
                for j in sips[i]:
                    bot_f.remove_member_from_queue(i.split('/')[1], j)
#                    await bot.send_message(message.chat.id, f"Удаление {i} из {j}")
                await bot.send_message(message.chat.id, f"{i} удалён из всех очередей")
                logbot.log_info(f"{i} удалён из всех очередей")
            await bot.send_message(message.chat.id, f"Все удалёны из всех очередей")
            await state.finish()
        else:
            await bot.send_message(message.chat.id, f"Нет доступа к удалению всех добавочных")
    elif message.text == 'Вернуться ко всем командам':
        await message.reply("Возврат ко всем командам", reply=False, reply_markup=kb.greet_kb_main)
        await state.finish()
    else:
        await bot.send_message(message.chat.id, 'Введите добавочный состоящий из трёх цифр')


@dp.message_handler(state=BotDialog_queues.queue_member_remove_state)
async def process_black_list_dur_and_baned(message: types.Message, state: FSMContext):
    if message.text.strip().lower() == 'да' or message.text.strip().lower() == 'lf':
        data = await state.get_data()
        for i in data['queues']:
            await bot.send_message(message.chat.id, f"Удаление из {i}")
            bot_f.remove_member_from_queue(data['member'], i)
        await bot.send_message(message.chat.id, f"Добавочный {data['member']} удалён из всех очередей", reply_markup=kb.greet_kb_main)
        await state.finish()
        logbot.log_info(f"""Пользователь {message.from_user.username}({message.from_user.id}) удалил добавочный {data['member']} из всех очередей""")
    elif message.text.strip().lower() == 'нет' or message.text.strip().lower() == 'ytn':
        await bot.send_message(message.chat.id, 'Ну нет так нет))', reply_markup=kb.greet_kb_main)
        await state.finish()
    elif message.text == 'Вернуться ко всем командам':
        await message.reply("Возврат ко всем командам", reply=False, reply_markup=kb.greet_kb_main)
        await state.finish()


@dp.message_handler(text=['Кто пропустил'])
async def process_missed(message: types.Message):
    await bot.send_message(message.chat.id,
                           'Они всё пропустили)',
                           reply_markup=kb.greet_kb_back)


@dp.message_handler(text=['Выгрузить звуковой файл по звонку'])
async def process_record(message: types.Message):
    await bot.send_message(message.chat.id,
                           """Введите информацию по звонку в формате ГОД-МЕСЯЦ-ДЕНЬ ЧАС:МИНУТА:СЕКУНДА НОМЕР \n Пример '2022-10-08 20:45:19 +7*****80623' или '2022-10-08 20:45:19 80623' \n Функция работает в тестовом режиме""",
                           reply_markup=kb.greet_kb_back)
    await BotDialog_records.records_state.set()


@dp.message_handler(state=BotDialog_records.records_state)
async def get_record_in_tg(message: types.Message, state: FSMContext):
    records = bot_f.get_id_record(message.text)
    if message.text == 'Вернуться ко всем командам':
        await message.reply("Возврат ко всем командам", reply=False, reply_markup=kb.greet_kb_main)
        await state.finish()
    else:
        for i in records:
            bot_f.get_record_from_minio(i[0])
        for i in records:
            bot_f.copy_record_from_aster(i[0])
        for i in records:
            await bot.send_audio(message.chat.id, open(f"{i[0]}", "rb"), reply_markup=kb.greet_kb_main)
            time.sleep(1)
            subprocess.check_output(f'rm ./{i[0]}', shell=True)
        for i in records:
            bot_f.delete_from_aster(i[0])
        await state.finish()


@dp.message_handler(text=['Для ОК'])
async def process_number(message: types.Message):
    await message.answer(f'Выберите команду', reply_markup=kb.greet_ok)


@dp.message_handler(text=['Статистика по анкетам'])
async def process_number(message: types.Message):
    await message.answer(f'Отправьте документ с анкетами', reply_markup=kb.greet_kb_back)
    await OkState.OkSt.set()


@dp.message_handler(state=OkState.OkSt, content_types=['document', 'text'])
async def load_file(message: types.Message, state: FSMContext):
    print(message.text)
    print(message.document)
    if message.text == 'Вернуться ко всем командам':
        await message.reply("Возврат ко всем командам", reply=False, reply_markup=kb.greet_kb_main)
        await state.finish()
    elif message.document is not None:
        src = f'docs/{message.document.file_name}' # путь до файла
        await message.document.download(destination_file=src) # это его скачивание
        gets = ok_f.ok_statistic(src)
        time.sleep(1)
        await message.answer_document(open(gets, 'rb'), reply_markup=kb.greet_kb_main)
        time.sleep(1)
        os.remove(gets)
        os.remove(src)
        logbot.log_info(f'Пользователь {message.chat.username} обработал файл {message.document.file_name}')
        await state.finish()


@dp.message_handler(text=['Кто завершил'])
async def process_number(message: types.Message):
    await bot.send_message(message.chat.id,
                           'Выберите направление звонка',
                           reply_markup=kb.construct_inline_buttons_cancel())


@dp.callback_query_handler(lambda c: c.data.startswith('cancel_'))
async def process_callback_cancel(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['dist'] = callback_query.data
        await callback_query.message.edit_text('Введите дату, время и номер через пробелы')
        await BotDialog_cancel.mess_state_2.set()


@dp.message_handler(state=BotDialog_cancel.mess_state_2)
async def process_number_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    dist = data['dist']
    if message.text == 'Вернуться ко всем командам':
        await message.reply("Возврат ко всем командам", reply=False, reply_markup=kb.greet_kb_main)
        await state.finish()
    else:
        answer = ok_f.get_info_numb(message.text, dist)
        await bot.send_message(message.chat.id, f"Нашлось звонков: {len(answer)}",
                               reply_markup=kb.construct_inline_buttons(answer))
        await state.finish()


@dp.callback_query_handler(lambda c: c.data.startswith('pbx2-01-'))
async def process_callback_kb1btn1(callback_query: types.CallbackQuery):
    try:
        code = callback_query.data
        answer = ok_f.get_info_event(code)
        await bot.send_message(callback_query.from_user.id, f'Звонок завершил {answer}', reply_markup=kb.greet_kb_main)
    except TypeError:
        await bot.send_message(callback_query.from_user.id, f'Нет информации по звонку', reply_markup=kb.greet_kb_main)
    await callback_query.message.delete()


@dp.message_handler(text=['тест','test'])
async def process_number(message: types.Message):
    await bot.send_message(message.chat.id,
                           message.contact.phone_number)


help_message = "Доступные команды: \n\
    /start - Начало работы с ботом\n\
    /help  - помощь\n\n\
    Большинство команд привязано к кнопкам"


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await message.reply(help_message)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)  # , on_startup=noon_print)

