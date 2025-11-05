import logging
import re
from enum import Enum
from typing import Any

import requests
from requests import HTTPError


class StrEnum(str, Enum):
    pass

    def __str__(self):
        return str(self.value)


class StrBooleanEnum(StrEnum):
    true = "true"
    false = "false"


class IntEnum(Enum):
    pass

    def __int__(self):
        return int(self.value)


def encode_url2(path):
    no_encode = "-_."
    encode = {
        "/": "!",
        ":": "(",
        "@": ")",
        "!": "'!",
        "(": "'(",
        "'": "''",
        "*": "'*"
    }
    encoded_path = ""
    for c in path:
        if c.isalnum() and c.isascii() or c in no_encode:
            encoded_path += c
        elif c in encode:
            encoded_path += encode[c]
        else:
            first = True
            for hex_enc in c.encode("utf-8").hex():
                if first:
                    encoded_path += f"*{hex_enc.upper()}"
                    first = False
                else:
                    encoded_path += hex_enc.upper()
                    first = True
    return encoded_path


def serialize_cdm(obj):
    """Cdm Serializer"""
    cdm = ""
    if issubclass(type(obj), dict):
        cdm += "("
        first = True
        for key in obj:
            if re.match(".*[^0-z].*", key):
                cdm += "'" if first else ".'"
                cdm += key.replace("'", "''")
                cdm += "'."
            else:
                cdm += key
            cdm += serialize_cdm(obj[key])
            if first:
                first = False
        cdm += ")"
    elif type(obj) is str:
        escaped = obj.replace("'", "''")
        cdm += f"'{escaped}'"
    elif issubclass(type(obj), StrEnum):
        escaped = obj.replace("'", "''")
        cdm += f"'{escaped}'"
    elif type(obj) is bool:
        cdm += "!T!" if obj else "!F!"
    elif issubclass(type(obj), list):
        cdm += "*"
        for idx, val in enumerate(obj):
            cdm += serialize_cdm(val)
            if idx < len(obj)-1:
                cdm += "."
        cdm += "-"
    elif obj is None:
        cdm += '!!'
    elif issubclass(type(obj), IntEnum):
        cdm += f"!{obj}!"
    else:
        cdm += f"!{obj}!"
    return cdm


def text(response: requests.Response) -> str:
    try:
        return response.content.decode("utf-8")
    except AttributeError:
        logging.error(f"Unable to extract text from response argument {response}")
    except ValueError:
        txt = response.text
        status = response.status_code
        logging.error(f"Unable to extract JSON from HTTP response [code:{status}].\n{txt}")
    raise RuntimeError(f"Unable to extract JSON data from {response.text}")


def json(response: requests.Response) -> Any:
    try:
        return response.json()
    except AttributeError:
        logging.error(f"Unable to extract JSON from response argument {response}")
    except ValueError:
        txt = text(response)
        status = response.status_code
        logging.error(f"Unable to extract JSON from HTTP response [code:{status}].\n{txt}")
    raise RuntimeError(f"Unable to extract JSON data from {text(response)}")


def check_status(response: requests.Response, *status: int) -> Any:
    try:
        if response.status_code not in status:
            raise HTTPError(f"Wrong HTTP Response. Should be in  {status}, got {response.status_code}", response=response)
        else:
            return
    except AttributeError:
        logging.error(f"Unable to extract status code from response argument {response}")
    raise RuntimeError(f"HTTP status control failed from response {response}")
