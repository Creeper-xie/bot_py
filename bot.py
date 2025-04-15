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
def ai(history):
    tries=0
    global user_contents
    generationConfig = {
        "response_mime_type": "application/json",
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "logic": {"type": "STRING"},
                "status": {"type":"STRING"},
                "reply": {"type": "ARRAY",
                          "items": {"type": "STRING"}
                          }
            }
        }
    } 

#    reqMsg= "{\"contents\": [{\"parts\":[{\"text\":" "\"" + msg["message"][0]["data"]["text"]+ "\"" "}]}]}"
    reqMsg={"system_instruction":{"parts":[{"text": prompt}]}, "contents" : history,"generationConfig": generationConfig}
    gemini_url= "{}?key={}".format(config["ai_url"],config["api_key"])
    while True:
        try:
            resp = requests.post(gemini_url,json.dumps(reqMsg))
            print(resp.text)
            resp=json.loads(resp.text)
            if "candidates" not in resp:
                return "呜.唔姆...喵♡（被塞口球力....）"
            respText=resp["candidates"][0]["content"]["parts"][0]["text"]
            return respText
        except:
            time.sleep(1)
            if tries >5:
                tries=0
                print("error")
                return "error"
            tries+=1
            continue

async def client():
    uri=config["bot_ws_uri"]
    global user_contents
    async with connect(uri,additional_headers={"Authorization": "Bearer {}".format(config["token"])}) as websocket:
        while True:
            msg = json.loads(await websocket.recv())
            if  "message_type" in msg and msg["message_type"] == "private" and msg["message"][0]["type"] == "text":
                print(msg)
                user_id = str(msg["user_id"])
                history=user_contents.get(user_id, [])
                history.append({"role":"user","parts" : [{"text": msg["sender"]["nickname"] + "：" + msg["message"][0]["data"]["text"]}]})
                rec = ai(history)
                if rec == "error":
                    continue
                history.append({"role":"model","parts" : [{"text": rec}]})
                user_contents[user_id]=history[-MAX_HISTORY_LENGTH:]
                rec = json.loads(rec)
                if rec["status"] == "skip":
                    print("跳过这次回复")
                    continue
#                sendMsg = json.loads("{\"action\": \"send_msg\",\"params\": {\"detail_type\":\"private\",\"user_id\":\"123456\",\"message\":[{\"type\"=\"text\",\"data\": {\"text\":\"" + rec["candidates"][0]["content"]["parts"][0]["text"] + "\"}}]}}")
                for i in rec["reply"]:
                    sendMsg = {
    "action": "send_msg",
    "params": {
        "detail_type": "private",
        "user_id": msg["user_id"],
        "message": [
            {
                "type": "text",
                "data": {
                    "text": i
                }
            }
        ]
    }
}
                    await websocket.send(json.dumps(sendMsg))
                    time.sleep(config["break_time"])



if __name__ == "__main__":
    with open("config.toml", "rb") as f:
        config = tomllib.load(f)
        prompt=str((open(config["prompt"], "r",encoding="utf-8")).read())
    asyncio.run(client())
