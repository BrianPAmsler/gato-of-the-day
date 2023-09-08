from __future__ import annotations
import json
import dateutil.parser
import bot

def save_client(client: bot.GatoClient, filename: str) -> None:
    f = open(filename, "w")
    serialized = json.dumps(list(client.channels), default=str)
    f.write(serialized)
    f.close()

def load_client(client: bot.GatoClient, filename: str) -> None:
    f = open(filename, "r")
    deserialized = json.loads(f.read())
    f.close()

    client.channels = set([(t[0], dateutil.parser.parse(t[1])) for t in deserialized])
