import datetime
import os
import re
import pandas as pd
from bot_functions import connect_db_with_all_permissions


my_head = ['Дата первого звонка', 'Звонок был на номер', 'Ответивший добавочный']


def ok_statistic(file):
    file_name = os.path.splitext(file)[0].split('/')[-1]
    data = pd.read_html(file)
    gg = {}
    numb_search = '4957809527|4957301035|4952288402|4993000007|4951340014|4953000680|' \
                  '8127036897|8122001734|8122002347|8122000017|8122003292|8122001248'
    data_index = 11
    mycursor = connect_db_with_all_permissions().cursor()
    for l in data:
        for m in l:
            gg.setdefault(m, [])
        for k in my_head:
            gg.setdefault(k, [])
        for ret in l.values:
            x, y = ret[data_index].split()
            r = '-'.join(x.split('.')[::-1])
            phone = str(ret[0])[-10:]
            sqlcom = f"""SELECT calldate as 'Дата первого звонка',
                                dst as 'Звонок был на номер',
                                userinterface as 'Ответивший добавочный'
                     FROM pbx.pbx_cdr
                     WHERE pbx_cdr.src LIKE '%{phone}'
                     AND calldate BETWEEN '{r} 00:00:00' AND '{r} {y}:59'
                     AND pbx_cdr.dst REGEXP '{numb_search}'
                     AND disposition = 'ANSWERED'
                     ORDER BY calldate
                     LIMIT 1"""
            mycursor.execute(sqlcom)
            result = mycursor.fetchone()
            if result is not None:
                for i, vad in enumerate(l):
                    gg[vad].append(ret[i])
                for j, sat in enumerate(my_head):
                    t = result[j]
                    if j == 0:
                        t = f"{'.'.join(str(result[j].date()).split('-')[::-1])} {result[j].time()}"
                    gg[sat].append(t)
    df = pd.DataFrame(gg)
    try:
        os.mkdir('excels')
    except:
        pass
    path_file = f'./excels/{file_name}.xlsx'
    df.to_excel(path_file, index=False)
    return path_file


def get_info_numb(searchdata: str, dist='cancel_in'):
    dicts = convert_str_to_dict(searchdata)
    info_list = {}
    headers = ['calldate', 'src', 'dst', 'userinterface', 'uniqueid']
    date_time = f"{'-'.join(dicts['date'])} {':'.join(dicts['time'])}"
    command = f"""SELECT {','.join(headers)}
                FROM pbx.pbx_cdr
                WHERE calldate BETWEEN '{date_time}:00' AND '{date_time}:59'
                AND pbx_cdr.{'src' if dist=='cancel_in' else 'dst'} LIKE '%{''.join(dicts['number'])[-5:]}'
                ORDER BY calldate DESC"""
    curs = connect_db_with_all_permissions().cursor()
    curs.execute(command)
    for i, vals in enumerate(curs.fetchall(), start=1):
        sort_info = {}
        for j, sort_vals in enumerate(vals):
            sort_info.setdefault(headers[j], str(sort_vals))
        info_list.setdefault(i, sort_info)
    return info_list


def get_info_event(searchid: str):
    command = f"""SELECT
                    case
                        when event = 'COMPLETEAGENT' then 'оператор'
                        when event = 'COMPLETECALLER' then 'звонящий'
                    end as 'Событие'
                FROM pbx.pbx_queue_log
                WHERE pbx_queue_log.event IN ('COMPLETEAGENT', 'COMPLETECALLER')
                AND pbx_queue_log.callid LIKE '{searchid}'
                ORDER BY time DESC"""
    curs = connect_db_with_all_permissions().cursor()
    curs.execute(command)
    datas = curs.fetchone()[0]
    return datas


def convert_str_to_dict(convertstr: str):
    info = ['date', 'time', 'number']
    data = {}
    for i, val in enumerate(convertstr.replace('+', '').split()):
        data.setdefault(info[i], re.split('\W+', val))
    return data
