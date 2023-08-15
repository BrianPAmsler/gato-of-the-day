import requests
import json

def get_gato():
    r = requests.get("https://api.thecatapi.com/v1/images/search")

    if r.status_code != 200:
        return None

    content = json.loads(r.content.decode('utf-8'))[0]

    return content["url"]

def get_perro():
    r = requests.get("https://api.thedogapi.com/v1/images/search")

    if r.status_code != 200:
        return None

    content = json.loads(r.content.decode('utf-8'))[0]

    return content["url"]

def get_carpincho():
    r = requests.get("https://api.capy.lol/v1/capybara?json=true")
    
    if r.status_code != 200:
        return None
    
    content = json.loads(r.content.decode('utf-8'))['data']
    
    return content["url"]

def get_zorro():
    r = requests.get("https://randomfox.ca/floof/?ref=apilist.fun")
    
    if r.status_code != 200:
        return None
    
    content = json.loads(r.content.decode('utf-8'))
    
    return content["image"]