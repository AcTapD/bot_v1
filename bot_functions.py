# -*- coding: utf-8 -*-
import pymysql
import time
import config
import paramiko
import bot_logging as logger
sec = time.time() - (60*60*24*30)
day, month, year = str(time.strftime('%d %m %Y', time.localtime(sec))).split()  # день, месяц, год


# Функция для получения нужной даты для работы
# Возвращается день, месяц, год
def set_day_for_calculate(daysAgo):
    sec = time.time() - (60 * 60 * 24 * daysAgo)
    day, month, year = str(time.strftime('%d %m %Y', time.localtime(sec))).split()  # день, месяц, год
    return day, month, year


# Для коннекта с базой для селектов
def connect_db():
    try:
        con = pymysql.connect(host=config.DB_HOST,
                              port=3306,
                              user=config.DB_USER,
                              password=config.DB_PASS,
                              charset='utf8mb4',
                              db=config.MAIN_DB)
        logger.log_info('Соединение с базой установлено')
        return con
    except:
        logger.log_error('Соединение с базой не установлено')


# Для коннекта с базой с правами админа для инсерта и апдейта
def connect_db_with_all_permissions():
    try:
        con = pymysql.connect(host=config.DB_HOST,
                              port=3306,
                              user=config.DB_USER_ADM,
                              password=config.DB_PASS_ADM,
                              charset='utf8mb4',
                              db=config.MAIN_DB)
        logger.log_info('Соединение с базой установлено')
        return con
    except:
        logger.log_error('Соединение с базой не установлено')


def chose_time(x=1/12):  # Функция для выбора даты (бана) (по умолчанию выбирается до конца следующего часа)
    g = time.localtime(time.time() + x * 24 * 60 * 60)
    d, m, y, h = time.strftime('%d %m %Y %H', g).split()
    return y, m, d, h  # Возврат года, месяца, дня, часа


# Для проверки введеной строки на наличие только цифр для раскрытия номера
def isint_for_get_number(x):
    try:
        if len(x) <= 5:
            int(x)
            return True
    except ValueError:
        return False


# Для проверки введеной строки на наличие только цифр для бана номера
def isint_for_add_BL(x):
    try:
        if len(x) == 10:
            int(x)
            return True
    except ValueError:
        return False


# Для раскрытия номера
# Принимает на себя последние 5 цифр номера (пока не указано что именно 5)
def get_number(num):
    con = connect_db()
    cur = con.cursor()
    cur.execute(f"SELECT DISTINCT src, calldate FROM pbx_cdr\
        WHERE src LIKE '%{num}'\
        AND calldate BETWEEN '{year}-{month}-{day} 00:00:00' AND NOW() \
        ORDER BY calldate desc \
        LIMIT 1")
    result = cur.fetchall()
    numb = ''
    # numb = f'За последние 3 дней нашлось {len(result)} звонков:\n'
    if len(result) == 0:
        numb = 'Нет номеров, проверьте правильность ввода цифр'
    for i in range(len(result)):
        for j in range(len(result[i])):
            if j == 0:
                numb += 'Номер: '
            elif j == 1:
                numb += '| Позвонил: '
            numb += str(result[i][j]) + ' '
        numb += '\n'
    con.close()
    return numb


# Для раскрытия номера для бана номера
# Принимает на себя последние 5 цифр номера (пока не указано что именно 5)
def get_number_for_BL(num):
    con = connect_db()
    cur = con.cursor()
    cur.execute(f"SELECT DISTINCT src, calldate FROM pbx_cdr\
        WHERE src LIKE '%{num}'\
        AND calldate BETWEEN '{year}-{month}-{day} 00:00:00' AND NOW() \
        ORDER BY calldate desc \
        LIMIT 1")
    result = cur.fetchall()
    # numb = ''
    # numb = f'За последние 3 дней нашлось {len(result)} звонков:\n'
    if len(result) == 0:
        numb = None
        timecall = None
    else:
        numb = int(result[0][0][-10:])
        timecall = str(result[0][1])
    con.close()
    return numb, timecall


# Для бана номера
# Принимает на себя (номер, причину бана, количество дней бана)
def ban_number(num, description, days):
    con = connect_db_with_all_permissions()
    cur = con.cursor()
    cur.execute(f"""
        SELECT * FROM pbx_blacklist
        WHERE callerid = '{num}'
    """)
    result = cur.fetchall()
    con.close()
    if len(result) > 0:
        update_ban_number(num, description, days)
    else:
        insert_ban_number(num, description, days)
    # con.close()
    return


# Функция для инсерта в бан лист
# Принимает на себя (номер, причину бана, количество дней бана)
def insert_ban_number(num, description, days):
    if days == 'час':
        y, m, d, h = chose_time()
    else:
        y, m, d, h = chose_time(int(days))
    con = connect_db_with_all_permissions()
    cur = con.cursor()
    cur.execute(f"""
        INSERT INTO pbx_blacklist(callerid, expiration_date, last_call_date, description)
        VALUES ('{num}', '{y}-{m}-{d} {h}:00:00', NOW(), '{description}')
    """)
    print(cur.fetchall())
    print('Был инсерт')
    con.commit()
    con.close()
    return


# Обновление таблицы с забаненными номерами
# Принимает на себя (номер, причину бана, количество дней бана)
def update_ban_number(num, description, days):
    if days == 'час':
        y, m, d, h = chose_time()
    else:
        y, m, d, h = chose_time(int(days))
    con = connect_db_with_all_permissions()
    cur = con.cursor()
    cur.execute(f"""
        UPDATE pbx_blacklist
        SET expiration_date = '{y}-{m}-{d} {h}:00:00', last_call_date = NOW(), description = '{description}'
        WHERE callerid = '{num}'
    """)
    print(cur.fetchall())
    print('Был апдейт')
    con.commit()
    con.close()
    return


# Функция для получения добавочных и очередей, в которых они есть
# Возвращает словарь key = добавочный, value = множество из очередей
def show_queues(sip):
    command = 'sudo asterisk -x "queue show"'
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=config.SSH_HOST,
                username=config.SSH_USER,
                password=config.SSH_PASS,
                port=config.SSH_PORT)
    session = ssh.get_transport().open_session()
    session.set_combine_stderr(True)
    session.get_pty()
    session.exec_command(command)
    stdin = session.makefile('wb', -1)
    stdout = session.makefile('rb', -1)
    stdin.write(config.SSH_PASS + '\n')
    stdin.flush()
    data = stdout.read().decode('utf-8').splitlines()
    members = dict()
    for i in data:
        if 'strategy' in i:
            queue = i.split(' ')[0]
        if 'SIP' in i:
            addM = i.strip().split(' ')[0]
            if addM not in members:
                members.setdefault(addM, {queue})
            else:
                members[addM].add(queue)
        if 'Callers' in i:
            queue = ''
    session.close()
    ssh.close()
    return members[f'SIP/{sip}']

def remove_member_from_queue(sip, queue):
    command = f'sudo asterisk -x "queue remove member SIP/{sip} from {queue}"'
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=config.SSH_HOST,
                username=config.SSH_USER,
                password=config.SSH_PASS,
                port=config.SSH_PORT)
    session = ssh.get_transport().open_session()
    session.set_combine_stderr(True)
    session.get_pty()
    session.exec_command(command)
    stdin = session.makefile('wb', -1)
    stdout = session.makefile('rb', -1)
    time.sleep(1)
    stdin.write(config.SSH_PASS + '\n')
    stdin.flush()
    stdout.read().decode('utf-8').splitlines()
    session.close()
    ssh.close()
    return


# Проверка на доступ к боту. Список достойных временно берется из списка
def check_permissions(id_telegram):
    permission = False
    for j in config.ALL_USERS:
        if id_telegram == j:
            permission = True
    return permission


# Функция для получения добавочных и очередей, в которых они есть
# Возвращает словарь key = добавочный, value = множество из очередей
def show_queues_all():
    command = 'sudo asterisk -x "queue show"'
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=config.SSH_HOST,
                username=config.SSH_USER,
                password=config.SSH_PASS,
                port=config.SSH_PORT)
    session = ssh.get_transport().open_session()
    session.set_combine_stderr(True)
    session.get_pty()
    session.exec_command(command)
    stdin = session.makefile('wb', -1)
    stdout = session.makefile('rb', -1)
    stdin.write(config.SSH_PASS + '\n')
    stdin.flush()
    data = stdout.read().decode('utf-8').splitlines()
    members = dict()
    for i in data:
        if 'strategy' in i:
            queue = i.split(' ')[0]
        if 'SIP' in i:
            addM = i.strip().split(' ')[0]
            if addM not in members:
                members.setdefault(addM, {queue})
            else:
                members[addM].add(queue)
        if 'Callers' in i:
            queue = ''
    session.close()
    ssh.close()
    return members


# Функция получения ID записи
def get_id_record(info):
    date = info.split()[0]
    time = info.split()[1]
    num = info.split()[2][-5:]
    con = connect_db()
    cur = con.cursor()
    cur.execute(f"""
            SELECT record FROM pbx_cdr
            WHERE calldate = '{date} {time}'
            AND (dst LIKE '%{num}'
            OR src LIKE '%{num}')
        """)
    result = cur.fetchall()
    con.close()
    return result


# Функция получения записи с минио
def get_record_from_minio(record):
    mc = '/var/lib/asterisk/agi-bin/custom/mc/mc'
    command = f"""sudo {mc} cp botminio/records/{record.split('_')[0]}/{record} /home/zazora/{record}"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=config.SSH_HOST,
                username=config.SSH_USER,
                password=config.SSH_PASS,
                port=config.SSH_PORT)
    session = ssh.get_transport().open_session()
    session.set_combine_stderr(True)
    session.get_pty()
    session.exec_command(command)
    stdin = session.makefile('wb', -1)
    stdout = session.makefile('rb', -1)
    time.sleep(1)
    stdin.write(config.SSH_PASS + '\n')
    stdin.flush()
    stdout.read().decode('utf-8').splitlines()
    session.close()
    ssh.close()
    return


# Функция копирования с машины астера на мою машину
def copy_record_from_aster(record):
    command = f"""scp /home/zazora/{record} zazora@pbx-apps-01.gazelkin.local:/var/www/tg_scripts/bot_v1"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=config.SSH_HOST,
                username=config.SSH_USER,
                password=config.SSH_PASS,
                port=config.SSH_PORT)
    session = ssh.get_transport().open_session()
    session.set_combine_stderr(True)
    session.get_pty()
    session.exec_command(command)
    stdin = session.makefile('wb', -1)
    stdout = session.makefile('rb', -1)
    time.sleep(2)
    stdin.write('Demon.1992\n')
    stdin.flush()
    stdout.read().decode('utf-8').splitlines()
    session.close()
    ssh.close()
    return


def delete_from_aster(record):
    command = f"""sudo rm /home/zazora/{record}"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=config.SSH_HOST,
                username=config.SSH_USER,
                password=config.SSH_PASS,
                port=config.SSH_PORT)
    session = ssh.get_transport().open_session()
    session.set_combine_stderr(True)
    session.get_pty()
    session.exec_command(command)
    stdin = session.makefile('wb', -1)
    stdout = session.makefile('rb', -1)
    time.sleep(1)
    stdin.write(config.SSH_PASS + '\n')
    stdin.flush()
    stdout.read().decode('utf-8').splitlines()
    session.close()
    ssh.close()
    return

