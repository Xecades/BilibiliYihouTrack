# code from https://github.com/ZJU-Turing/TuringDingBot/blob/master/src/utils/dingtalk.py

import time
import hmac
import hashlib
import base64
import json
import requests
import urllib.parse
from loguru import logger as L

from secret import DINGTALK_SEND_URL, DINGTALK_SIGNATURE


def send_dingtalk_message(message: str):
    timestamp, sign = get_timestamp_and_sign()
    url = DINGTALK_SEND_URL + f"&timestamp={timestamp}&sign={sign}"
    data = {'msgtype': 'text', 'text': {'content': message}}
    data = json.dumps(data, ensure_ascii=False).encode("utf-8")
    res = requests.post(
        url,
        data=data,
        headers={'Content-Type': 'application/json;charset=utf-8'}
    )
    if res.status_code != 200:
        L.error("Failed to send dingtalk message")
    elif res.json()["errcode"] != 0:
        L.error(f"error message: {res.json()['errmsg']}")
    L.info(f"Dingtalk message sent successfully: {message}")


def get_timestamp_and_sign() -> tuple:
    timestamp = str(round(time.time() * 1000))
    secret = DINGTALK_SIGNATURE.encode("utf-8")
    bytes_to_sign = "{}\n{}".format(
        timestamp, DINGTALK_SIGNATURE).encode("utf-8")
    hmac_code = hmac.new(secret, bytes_to_sign,
                         digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return timestamp, sign


if __name__ == "__main__":
    send_dingtalk_message("Hello, this is a test message from the script!")
