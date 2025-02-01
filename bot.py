import sys
import json
import asyncio
import requests

from websockets.asyncio.client import connect


if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

def ai(msg):
    msg1= "{\"contents\": [{\"parts\":[{\"text\":" "\"" + msg+ "\"" "}]}]}"
    print(msg1)
    data = json.loads(msg1)
    print(data)
    gemini_url= "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={}".format(config["api_key"])
    resp = requests.post(gemini_url,data)
    print(resp.text)

async def client(config):
    uri=config["bot_ws_uri"]
    async with connect(uri,additional_headers={"Authorization": "Bearer {}".format(config["token"])}) as websocket:
        while True:
            msg = await websocket.recv()
            print(msg)
#            ai(msg)

if __name__ == "__main__":
    with open("config.toml", "rb") as f:
        config = tomllib.load(f)
    asyncio.run(client(config))
