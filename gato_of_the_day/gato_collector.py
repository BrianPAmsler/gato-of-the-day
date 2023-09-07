import requests
import json
from json.scanner import py_make_scanner
from json.decoder import JSONArray

class ArrayAsDictDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def parse_array(*_args, **_kwargs):
            values, end = JSONArray(*_args, **_kwargs)
            array_dict = {}
            for (i, e) in enumerate(values):
                array_dict[str(i)] = e

            return array_dict, end

        self.parse_array = parse_array
        self.scan_once = py_make_scanner(self)

api_info = []

def load_api_info():
    global api_info

    file = open("api_info.json", 'r')
    data_string = file.read()
    file.close()

    api_info = json.loads(data_string)

def get_pic(name):
    if name not in api_info:
        return None
    
    info = api_info[name]

    path: str = info["json_path"]
    keys = path.split('/')

    r = requests.get(info['url'])

    if r.status_code != 200:
        return None

    decoder = ArrayAsDictDecoder()
    content_string = r.content.decode()
    content = decoder.decode(content_string)

    obj = content
    for key in keys:
        obj = obj[key]
    
    return obj

def is_valid_name(name):
    return name in api_info

def names():
    return api_info

def get_title(name):
    if name not in api_info:
        return None
    
    info = api_info[name]
    title = info["title"]

    return title