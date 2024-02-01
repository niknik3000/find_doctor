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
import uuid


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
                # кусок ниже не трогать так как если возвращается str, то при преобразовании в dict списка нет
                if isinstance(d, dict):
                    spec_data[d['DoctorName']] = d['ListDateRecords']['DateRecords']
                    spec_data['DoctorId'] = d['DoctorId']
                else:
                    spec_data[json.loads(get_info)['GetScheduleTableResponse']['ListScheduleRecord']['ScheduleRecord']['DoctorName']] = json.loads(get_info)['GetScheduleTableResponse']['ListScheduleRecord']['ScheduleRecord']['ListDateRecords']['DateRecords']
                    spec_data["DoctorId"] = json.loads(get_info)['GetScheduleTableResponse']['ListScheduleRecord']['ScheduleRecord']['DoctorId']
        except Exception as ex:
            logging.error(f"EXCEPTION: {ex}")
            logging.error(f"RESPONSE ===> {get_info} <===")
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

    def __headers(self, med_id, specId):
        return {
            'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0',
            'Accept-Language' : 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Content-Type' : 'application/json',
            'X-Requested-With' : 'XMLHttpRequest',
            'Origin' : 'https://intermed76.ru',
            'DNT' : '1',
            'Connection' : 'keep-alive',
            'Referer' : f'https://intermed76.ru/?moId={med_id}&specId={specId}',
            'Cookie': f'JSESSIONID={gen_uuid}',
            'Sec-Fetch-Dest' : 'empty',
            'Sec-Fetch-Mode' : 'cors',
            'Sec-Fetch-Site' : 'same-origin'
        }

    def __get_info(self, DateFrom, DateTo, specId):
        """
        Get info from server
        """
        address = 'https://intermed76.ru/intermed/findSchedulesTable'
        data2send = {"GetScheduleTableRequest":{"RecordSource":"epgu","RegId":f"{med_id}","DateFrom":f'{DateFrom}',"DateTo":f'{DateTo}',"ListSpecs":[{"Spec":f'{specId}'}]}}
        send_data = requests.post(address, headers=self.__headers(med_id, specId), data=json.dumps(data2send), verify=False, timeout=180)
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
                doc_id = get_spec_info["DoctorId"]
                if who in name:
                    free_tickets_dict[name] = {}
                    for _item in dates:
                        if isinstance(_item, str):
                            _item = json.loads(_item)
                        if _item['FreeRecords'] > 0 and not len(_item['Comment']) > 0:
                            date_of = _item['Day'].split('T')[0]
                            free_tickets_dict[name][date_of] = {}
                            time = self.time_request(date_of, doc_id, family[who])
                            free_tickets_dict[name][date_of]['FreeRecords'] = _item['FreeRecords']
                            free_tickets_dict[name][date_of]['FreeTime'] = time
                        # elif isinstance(_item, str):
                        #     if dates['FreeRecords'] > 0 and not len(dates['Comment']) > 0:
                        #         date_of = dates['Day'].split('T')[0]
                        #         time = self.time_request(date_of, doc_id, family[who])
                        #         free_tickets_dict[name][date_of]['FreeRecords'] = dates['FreeRecords']
                        #         free_tickets_dict[name][date_of]['FreeTime'] = time
        logging.debug(f'Get DATA: {free_tickets_dict}')
        free_tickets_dict = self.__sort_dict(free_tickets_dict)
        return free_tickets_dict # {'Николаева Татьяна Александровна (Детская поликлиника №2)': {'2024-02-01': 1, '2024-02-12': 6}}

    def time_request(self, date, doc_id, spec_id):
        """"""
        address = "https://intermed76.ru/intermed/findScheduleFreeSlots"
        request_dict = {
            "GetScheduleFreeSlotsRequest": {
                "DateRequest": f"{date}",
                "DepartOid": f"{med_id}",
                "DoctorId": f"{doc_id}",
                "SpecId": f"{spec_id}"
            }
        }
        send_data = requests.post(address, headers=self.__headers(med_id, spec_id), data=json.dumps(request_dict), verify=False, timeout=180)
        if send_data.status_code == 200:
            return send_data.json()["GetScheduleFreeSlotsResponse"]["Free_Slots"]
        else:
            raise ConnectionError(f"Не получили ответ от {address} код {send_data.status_code}")

def createParser():
    """Парсим аргументы запуска скрипта"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--name', default='Николаева', help="Фамилия врача")
    parser.add_argument('-f', '--config_file', default='11347.json', help="Файл с инфой о врачах, имя файла - id заведения")
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
        gen_uuid = uuid.uuid4().hex.upper()
        seconds2check = randint(60, 90)
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
                    sended_tickets[key] = {}
                if value:
                    if (
                        (len([x for x in get_info.keys() if params.name in x]) > 0 and params.name in key)
                        or (len([x for x in get_info.keys() if params.name in x]) == 0)
                        ):
                        for _date, records_info in value.items():
                            records_count = records_info["FreeRecords"]
                            records_time = sorted(records_info["FreeTime"].split(';'))
                            if not _date in sended_tickets[key]:
                                send_data += f"=========\n{_date}\nCвободно явок: {records_count}\nСвободное время:{records_time}\n"
                                sended_tickets[key][_date] = records_time
                            else:
                                free_time_diff =  list(set(records_time) - set(sended_tickets[key][_date]))
                                if not free_time_diff:
                                    logging.info(f"По дате {_date} и времени {free_time_diff} уже отсылалось оповещение {sended_tickets[key]}")
                                else:
                                    send_data += f"=========\n{_date} появилось {len(free_time_diff)} явок\nСвободное время:{free_time_diff}\n"
                else:
                    logging.info(f"Нечего отсылать {get_info}")
            if send_data:
                send_data = params.name + '\n' + send_data + '\n' + f"https://intermed76.ru/?moId={med_id}&specId={family[params.name]}"
                common.send_doctors(send_data)
        time.sleep(seconds2check)

# ============================================================================================
# общий запрос https://intermed76.ru/intermed/findSpecs
# вида
# {
# 	"GetServiceSpecsInfoRequest": {
# 		"MO_Id": "1.2.643.5.1.13.13.12.2.76.11381",
# 		"Reg_Id": "11347"
# 	}
# }
# вернет
# {
# 	"GetServiceSpecsInfoResponse": {
# 		"Session_ID": "8fca8848-cb6b-4aec-875b-647dba47e2fc",
# 		"ListServiceSpecs": {
# 			"ServiceSpec": [
# 				{
# 					"ServiceSpec_Id": 79,
# 					"ServiceSpec_Name": "Гастроэнтерология"
# 				},
# 				{
# 					"ServiceSpec_Id": 10,
# 					"ServiceSpec_Name": "Дерматовенерология"
# 				},
# 				{
# 					"ServiceSpec_Id": 81,
# 					"ServiceSpec_Name": "Детская кардиология"
# 				},
# 				{
# 					"ServiceSpec_Id": 11,
# 					"ServiceSpec_Name": "Детская хирургия"
# 				},
# 				{
# 					"ServiceSpec_Id": 83,
# 					"ServiceSpec_Name": "Детская эндокринология"
# 				},
# 				{
# 					"ServiceSpec_Id": 14,
# 					"ServiceSpec_Name": "Неврология"
# 				},
# 				{
# 					"ServiceSpec_Id": 19,
# 					"ServiceSpec_Name": "Оториноларингология"
# 				},
# 				{
# 					"ServiceSpec_Id": 22,
# 					"ServiceSpec_Name": "Педиатрия"
# 				},
# 				{
# 					"ServiceSpec_Id": 208,
# 					"ServiceSpec_Name": "Стоматология"
# 				},
# 				{
# 					"ServiceSpec_Id": 28,
# 					"ServiceSpec_Name": "Травматология и ортопедия"
# 				}
# 			]
# 		},
# 		"Error": {
# 			"errorDetail": {
# 				"errorCode": 0,
# 				"errorMessage": ""
# 			}
# 		}
# 	}
# }
# ============================================================================================
# запрос на https://intermed76.ru/intermed/findSchedulesTable
# {
# 	"GetScheduleTableRequest": {
# 		"DateFrom": "2024-01-31",
# 		"DateTo": "2024-02-14",
# 		"ListSpecs": [
# 			{
# 				"Spec": "19"
# 			}
# 		],
# 		"RecordSource": "epgu",
# 		"RegId": "11347"
# 	}
# }
# вернет
# {
# 	"GetScheduleTableResponse": {
# 		"ListScheduleRecord": {
# 			"ScheduleRecord": {
# 				"DoctorId": 12453670345,
# 				"DoctorName": "Николаева Татьяна Александровна (Детская поликлиника №2)",
# 				"DoctorSpec": 19,
# 				"DoctorSpecName": "Оториноларингология",
# 				"Area": "",
# 				"Cabinet": 30,
# 				"ListDateRecords": {
# 					"DateRecords": [
# 						{
# 							"Day": "2024-02-03T00:00:00+03:00",
# 							"Time": "09:00 - 14:00",
# 							"AllRecords": 27,
# 							"FreeRecords": 0,
# 							"Comment": ""
# 						},
# 						{
# 							"Day": "2024-02-01T00:00:00+03:00",
# 							"Time": "09:00 - 15:00",
# 							"AllRecords": 26,
# 							"FreeRecords": 1,
# 							"Comment": ""
# 						},
# 						{
# 							"Day": "2024-02-02T00:00:00+03:00",
# 							"Time": "09:00 - 15:00",
# 							"AllRecords": 32,
# 							"FreeRecords": 0,
# 							"Comment": ""
# 						},
# 						{
# 							"Day": "2024-02-06T00:00:00+03:00",
# 							"Time": "09:00 - 15:00",
# 							"AllRecords": 32,
# 							"FreeRecords": 0,
# 							"Comment": ""
# 						},
# 						{
# 							"Day": "2024-02-08T00:00:00+03:00",
# 							"Time": "09:00 - 15:00",
# 							"AllRecords": 26,
# 							"FreeRecords": 0,
# 							"Comment": ""
# 						},
# 						{
# 							"Day": "2024-02-09T00:00:00+03:00",
# 							"Time": "09:00 - 15:00",
# 							"AllRecords": 32,
# 							"FreeRecords": 0,
# 							"Comment": ""
# 						},
# 						{
# 							"Day": "2024-01-31T00:00:00+03:00",
# 							"Time": "12:00 - 16:00",
# 							"AllRecords": 22,
# 							"FreeRecords": 0,
# 							"Comment": ""
# 						},
# 						{
# 							"Day": "2024-02-05T00:00:00+03:00",
# 							"Time": "13:00 - 19:00",
# 							"AllRecords": 32,
# 							"FreeRecords": 0,
# 							"Comment": ""
# 						},
# 						{
# 							"Day": "2024-02-12T00:00:00+03:00",
# 							"Time": "13:00 - 19:00",
# 							"AllRecords": 32,
# 							"FreeRecords": 6,
# 							"Comment": ""
# 						}
# 					]
# 				}
# 			}
# 		},
# 		"Error": {
# 			"errorDetail": {
# 				"errorCode": 0,
# 				"errorMessage": ""
# 			}
# 		}
# 	}
# }
# ============================================================================================
# запрос на получение времени приема по врачу JSON на https://intermed76.ru/intermed/findScheduleFreeSlots
# {
# 	"GetScheduleFreeSlotsRequest": {
# 		"DateRequest": "2024-02-12",
# 		"DepartOid": "11347",
# 		"DoctorId": "12453670345",
# 		"SpecId": "19"
# 	}
# }
# вернет
# {
# 	"GetScheduleFreeSlotsResponse": {
# 		"Free_Slots": "14:00;14:12;14:36;14:48;15:12;15:36",
# 		"Status_Code": 0
# 	}
# }
# ============================================================================================