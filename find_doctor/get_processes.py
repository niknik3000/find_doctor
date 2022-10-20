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
    doctors_need2run = (json.loads(config_file))["doctors_to_find"]
    all_doctors = (json.loads(config_file))["all_doctors"]
    pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]
    already_running_scripts = dict()
    for pid in pids:
        try:
            data = open(os.path.join('/proc', pid, 'cmdline'), 'r').read().split('\0')
            if len(data) >= 5 and data[3] in all_doctors:
                already_running_scripts[data[3]] = pid
        except IOError:  # proc has already terminated
            continue
    if len(already_running_scripts) != len(doctors_need2run):
        for _name in doctors_need2run:
            if not _name in already_running_scripts:
                logging.warning(f"Скрипт по {_name} не найден, запускаем")
                # common.send_statistics(f"Скрипт по {_name} не найден, запускаем")
                subprocess.Popen(['python3.8', START_PATH, '--name', _name, '--days_count', '20'])
                time.sleep(randint(10, 20))
        for _name in already_running_scripts:
            if not _name in doctors_need2run:
                _send_str = f"Скрипт по {_name} больше не нужен"
                logging.warning(_send_str)
                common.send_statistics(_send_str)
                try:
                    subprocess.Popen(['kill', '-9', already_running_scripts[_name]])
                except Exception as e:
                    _send_str = f"Скрипт по {_name} прибить не удалось: {str(e)}\nПрибей руками sudo kill -9 {already_running_scripts[_name]}"
                    logging.warning(_send_str)
                    # common.send_statistics(_send_str)
                time.sleep(randint(10, 20))
    else:
        logging.info("Все необходимые скрипты запущены")
        time.sleep(60)
