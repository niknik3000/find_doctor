import requests
import json
import datetime
import time
from dateutil.relativedelta import relativedelta
import logging
import argparse
import common
import os
from random import randint


logging.basicConfig(level=logging.INFO, format='[%(asctime)s][%(levelname)s] %(message)s', datefmt='%d-%b-%y %H:%M:%S')
console = logging.StreamHandler()
console.setLevel(logging.INFO)

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))



class Doctors:
    """docstring"""
    
    def __init__(self, family):
        """Constructor"""
        self.family = family

    def __get_specialist_info(self, DateFrom, DateTo, specId, who):
        spec_data = {}
        get_info = self.__get_info(str(DateFrom), str(DateTo), specId).decode("utf-8")
        try:
            if not json.loads(get_info)['GetScheduleTableResponse']['ListScheduleRecord']:
                logging.warning(f"От сервер пришел пустой ответ, у специалиста нет приема в указанном периоде, расширьте диапазон поиска!! {get_info}")
            for d in json.loads(get_info)['GetScheduleTableResponse']['ListScheduleRecord']['ScheduleRecord']:
                if isinstance(d, (dict)):
                    spec_data[d['DoctorName']] = d['ListDateRecords']['DateRecords']
                else:
                    spec_data[json.loads(get_info)['GetScheduleTableResponse']['ListScheduleRecord']['ScheduleRecord']['DoctorName']] = json.loads(get_info)['GetScheduleTableResponse']['ListScheduleRecord']['ScheduleRecord']['ListDateRecords']['DateRecords']
        except Exception as ex:
            logging.info(f"RESPONSE ===> {get_info} <===")
            if self.is_valid_json(get_info):
                if isinstance(json.loads(get_info).get('GetScheduleTableResponse', {}).get('Error', {}).get("errorDetail", {}).get("errorCode"), int):
                    err_num = json.loads(get_info).get('GetScheduleTableResponse').get('Error').get("errorDetail").get("errorCode")
                    err_msg = json.loads(get_info).get('GetScheduleTableResponse').get('Error').get("errorDetail").get("errorMessage")
                    if err_num != 0:
                        common.send_statistics(f"Ошибка при обработке запроса на стороне сервера для {who}:\nИсключение:{ex}\nТекст ошибки:{err_msg}\nТело ответа:{get_info}")
                else:
                    common.send_statistics(f"Исключение при обработке запроса для {who}:\nИсключение:{ex}\nТело ответа:{get_info}\nТип ответа:{type(get_info)}")
        return spec_data

    def is_valid_json(self, inc_json) -> bool:
        try:
            json.loads(inc_json)
        except ValueError as e:
            return False
        return True


    def __get_info(self, DateFrom, DateTo, specId):
        """
        Get info from server
        """
        # logging.info("specId " + str(specId))
        address = 'https://intermed76.ru/intermed/findSchedulesTable'
        headers = {
            'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0',
            'Accept-Language' : 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Content-Type' : 'application/json',
            'X-Requested-With' : 'XMLHttpRequest',
            'Origin' : 'https://intermed76.ru',
            'DNT' : '1',
            'Connection' : 'keep-alive',
            'Referer' : f'https://intermed76.ru/?moId={med_id}&specId={specId}',
            'Cookie' : 'JSESSIONID=4577D2D0D88BED2751B76F4F78C3F5C7',
            'Sec-Fetch-Dest' : 'empty',
            'Sec-Fetch-Mode' : 'cors',
            'Sec-Fetch-Site' : 'same-origin'
        }
        data2send = {"GetScheduleTableRequest":{"RecordSource":"epgu","RegId":f"{med_id}","DateFrom":f'{DateFrom}',"DateTo":f'{DateTo}',"ListSpecs":[{"Spec":f'{specId}'}]}}
        send_data = requests.post(address, headers=headers, data=json.dumps(data2send), verify=False, timeout=180)
        return send_data.content


    def get_specialist_work_time(self, who):
        work_time_dict = {}
        for _item in self.__get_specialist_info(DateFrom, DateTo, family[who], who):
            work_time_dict[_item['Day'].split('T')[0]] = _item['Time']
        logging.debug(f"work_time_dict: {work_time_dict}")
        return work_time_dict

    def __sort_dict(self, dict2sort):
        today_ = datetime.datetime.today()
        ret_dict = {}
        get_dates = []
        for x in dict2sort.keys():
            get_dates.append(x) 
        get_dates.sort()
        for _item in get_dates:
            for _key, _value in dict2sort.items():
                if _key == _item:
                    ret_dict[_key] = _value
        return ret_dict


    def get_specialist_free_tickets(self, days_count, who):
        get_spec_info = self.__get_specialist_info(DateFrom, DateTo, family[who], who)
        free_tickets_dict = {}
        if get_spec_info:
            for name, dates in get_spec_info.items():
                free_tickets_dict[name] = {}
                for _item in dates:
                    if isinstance(_item, dict):
                        if _item['FreeRecords'] > 0 and not len(_item['Comment']) > 0:
                            free_tickets_dict[name][_item['Day'].split('T')[0]] = _item['FreeRecords']
                    elif isinstance(_item, str):
                        if dates['FreeRecords'] > 0 and not len(dates['Comment']) > 0:
                            free_tickets_dict[name][dates['Day'].split('T')[0]] = dates['FreeRecords']
        logging.debug(f'Get DATA: {free_tickets_dict}')
        free_tickets_dict = self.__sort_dict(free_tickets_dict)
        return free_tickets_dict

def createParser():
    """Парсим аргументы запуска скрипта"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--name', default='Симановская', help="Фамилия врача")
    parser.add_argument('-f', '--config_file', default='30058.json', help="Файл с инфой о врачах, имя файла - id заведения")
    parser.add_argument('-c', '--days_count', default=20, help="На сколько дней вперед ищем, по умолчанию 20 дней от текущей даты")
    parser.add_argument('-d', '--debug', action='store_false', help="Выводить отладочный лог")
    return parser


if __name__ == "__main__":
    sended_tickets = {}
    params = createParser().parse_args()
    family = (json.loads(open(os.path.join(CURRENT_DIR, params.config_file)).read()))["all_doctors"]
    med_id = params.config_file.replace(".json", "")
    doctor = Doctors(family)
    get_info = {}
    start_date =  datetime.date.today()
    if params.debug:
        logging.info("Logging level is DEBUG")
        logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s', datefmt='%I:%M:%S %p')
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s', datefmt='%I:%M:%S %p')
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
    if not params.name in family.keys():
        raise ValueError(f"Специалист должен быть в списке {family.keys()}")
    common.send_statistics(f"Поиск явок для {params.name}")
    while True:
        seconds2check = randint(30, 50)
        send_data = ''
        delta = (datetime.datetime.strptime(str(start_date), '%Y-%m-%d') -  datetime.datetime.today()).days
        if delta < -1: # КОКОСТЫЛЬНЕКО раз в сутки обнуляем списки обработанных дат
            start_date =  datetime.date.today()
            sended_tickets = {}
            # logging.info("С обнулением!!!")
        DateFrom = datetime.date.today() + relativedelta(days=1)
        DateTo = datetime.date.today() + relativedelta(days=int(params.days_count))
        logging.info(f'Ищем явки для {params.name} c {DateFrom} по {DateTo}')
        get_info = doctor.get_specialist_free_tickets(params.days_count, params.name)
        if get_info:
            for key, value in get_info.items():
                if not sended_tickets.get(key):
                    sended_tickets[key] = []
                if value:
                    if (
                        (len([x for x in get_info.keys() if params.name in x]) > 0 and params.name in key)
                        or (len([x for x in get_info.keys() if params.name in x]) == 0)
                        ):
                        for _date, _number in value.items():
                            if not _date in sended_tickets[key]:
                                send_data += f"{_date} cвободно {_number} явок\n"
                                sended_tickets[key].append(_date)
                            else:
                                logging.info(f"По дате {_date} уже отсылалось оповещение {sended_tickets[key]}")
                else:
                    logging.info(f"Нечего отсылать {get_info}")
            if send_data:
                send_data = params.name + '\n' + send_data + '\n' + f"https://intermed76.ru/?moId={med_id}&specId={family[params.name]}"
                common.send_doctors(send_data)
            # else:
            #     logging.info(f'No avaible tickets in {params.days_count} days, retry after {seconds2check} seconds\nDEBUG: {get_info}')
        time.sleep(seconds2check)


# TODO: доделать получение времени явки запросом curl 'https://intermed76.ru/intermed/findScheduleFreeSlots' \
#   -H 'Connection: keep-alive' \
#   -H 'Pragma: no-cache' \
#   -H 'Cache-Control: no-cache' \
#   -H 'sec-ch-ua: "Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"' \
#   -H 'Accept: application/json, text/javascript, */*; q=0.01' \
#   -H 'DNT: 1' \
#   -H 'X-Requested-With: XMLHttpRequest' \
#   -H 'sec-ch-ua-mobile: ?0' \
#   -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36' \
#   -H 'Content-Type: application/json' \
#   -H 'Origin: https://intermed76.ru' \
#   -H 'Sec-Fetch-Site: same-origin' \
#   -H 'Sec-Fetch-Mode: cors' \
#   -H 'Sec-Fetch-Dest: empty' \
#   -H 'Referer: https://intermed76.ru/?moId=11347&specId=14' \
#   -H 'Accept-Language: ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7' \
#   -H 'Cookie: JSESSIONID=153938F40AC10F30BB6D8CB46917B29D' \
#   --data-raw '{"GetScheduleFreeSlotsRequest":{"DepartOid":"11347","SpecId":"14","DoctorId":"04562285963","DateRequest":"2021-09-30"}}' \
#   --compressed