import requests
import json

def get_gato():
    r = requests.get("https://api.thecatapi.com/v1/images/search")

    if r.status_code != 200:
        return None

    content = json.loads(r.content.decode('utf-8'))[0]
    print(content)

    return content["url"]