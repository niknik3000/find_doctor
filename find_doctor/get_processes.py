#!/usr/bin/env python3
import os, subprocess, common, time, logging
from random import randint
import json


logging.basicConfig(level=logging.INFO, format='[%(asctime)s][%(levelname)s] %(message)s', datefmt='%d-%b-%y %H:%M:%S')
console = logging.StreamHandler()
console.setLevel(logging.INFO)

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
START_PATH = os.path.join(CURRENT_DIR, 'find_doctor.py')
while True:
    config_file = open(os.path.join(CURRENT_DIR, "find_doctors.json")).read()
    find_pattern = (json.loads(config_file))["doctors_to_find"]
    pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]
    founded_data = []
    for pid in pids:
        try:
            data = open(os.path.join('/proc', pid, 'cmdline'), 'r').read().split('\0')
            if len(data) >= 5 and data[3] in find_pattern:
                founded_data.append(data[3])
        except IOError: # proc has already terminated
            continue
    if len(founded_data) < len(find_pattern):
        for _name in find_pattern:
            if not _name in founded_data:
                logging.warning(f"Скрипт по {_name} не найден, запускаем")
                try:
                    common.send_statistics(f"Скрипт по {_name} не найден, запускаем")
                except Exception as e:
                    logging.error(f"Ошибка {str(e)}")
                subprocess.Popen(['python3.8', START_PATH, '--name', _name, '--days_count', '20'])
                time.sleep(randint(10, 20))
    else:
        logging.info("Все необходимые скрипты запущены")
        time.sleep(600)
