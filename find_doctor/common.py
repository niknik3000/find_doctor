import requests
from pykeepass import PyKeePass
import base64
import os


def unpack():
    base64_bytes = 'ZEZsSzM4Sk1tXzgzamtMS2tzS2xzYUFBc3NBQXFjY18p'.encode('ascii')
    message_bytes = base64.b64decode(base64_bytes)
    return message_bytes.decode('ascii')


def get_bot():
    current_dir = os.path.abspath(os.path.dirname(__file__))
    kp = PyKeePass(os.path.join(current_dir, 'tele.kdbx'), password=unpack(), keyfile=os.path.join(current_dir, "token",
                                                                                                   "tele.tok"))
    group = kp.find_groups(name='tele', first=True)
    return group.entries[0].username, group.entries[0].password


def send_statistics(send_data):
    l, p = get_bot()
    requests.get(f"https://api.telegram.org/{l}:{p}/sendMessage?chat_id=-517903641", json={'text': send_data})


def send_doctors(send_data):
    l, p = get_bot()
    requests.get(f"https://api.telegram.org/{l}:{p}/sendMessage?chat_id=-510430964", json={'text': send_data})
