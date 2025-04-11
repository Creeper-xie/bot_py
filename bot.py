import sys
import json
import asyncio
from typing import Deque
import requests
import time

from requests.models import ContentDecodingError
from websockets.asyncio.client import connect


if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

MAX_HISTORY_LENGTH = 30
user_contents = {}
def ai(msg):
    tries=0
    global user_contents
    user_id = str(msg["user_id"])
    history=user_contents.get(user_id, [])
    history.append({"role":"user","parts" : [{"text": msg["message"][0]["data"]["text"]}]})
#    reqMsg= "{\"contents\": [{\"parts\":[{\"text\":" "\"" + msg["message"][0]["data"]["text"]+ "\"" "}]}]}"
    reqMsg={"contents" : history}
    gemini_url= "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-thinking-exp:generateContent?key={}".format(config["api_key"])
    while True:
        try:
            resp = requests.post(gemini_url,json.dumps(reqMsg))
            print(resp.text)
            resp=json.loads(resp.text)
            if "candidates" not in resp:
                return "error"
            respText=resp["candidates"][0]["content"]["parts"][0]["text"]
            history.append({"role":"model","parts" : [{"text": respText}]})
            user_contents[user_id]=history[-MAX_HISTORY_LENGTH:]
            return respText
        except:
            time.sleep(1)
            if tries >5:
                return "error"
            tries+=1
            continue

async def client(config):
    uri=config["bot_ws_uri"]
    async with connect(uri,additional_headers={"Authorization": "Bearer {}".format(config["token"])}) as websocket:
        while True:
            msg = json.loads(await websocket.recv())
            if  "message_type" in msg and msg["message_type"] == "private" and msg["message"][0]["type"] == "text":
                print(msg)
                rec = ai(msg)
                if rec == "error":
                    continue
#                sendMsg = json.loads("{\"action\": \"send_msg\",\"params\": {\"detail_type\":\"private\",\"user_id\":\"123456\",\"message\":[{\"type\"=\"text\",\"data\": {\"text\":\"" + rec["candidates"][0]["content"]["parts"][0]["text"] + "\"}}]}}")
                sendMsg = {
    "action": "send_msg",
    "params": {
        "detail_type": "private",
        "user_id": msg["user_id"],
        "message": [
            {
                "type": "text",
                "data": {
                    "text": rec
                }
            }
        ]
    }
}
                await websocket.send(json.dumps(sendMsg))



if __name__ == "__main__":
    with open("config.toml", "rb") as f:
        config = tomllib.load(f)
    asyncio.run(client(config))
