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
    reqMsg= "{\"contents\": [{\"parts\":[{\"text\":" "\"" + msg["message"][0]["data"]["text"]+ "\"" "}]}]}"
    gemini_url= "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-thinking-exp:generateContent?key={}".format(config["api_key"])
    while True:
        try:
            resp = requests.post(gemini_url,reqMsg)
            print(resp.text)
            return json.loads(resp.text)
        except requests.exceptions.HTTPError as e:
            print(e)
            continue

async def client(config):
    uri=config["bot_ws_uri"]
    async with connect(uri,additional_headers={"Authorization": "Bearer {}".format(config["token"])}) as websocket:
        while True:
            msg = json.loads(await websocket.recv())
            if  "message_type" in msg and msg["message_type"] == "private":
                print(msg)
                rec = ai(msg)
#                sendMsg = json.loads("{\"action\": \"send_msg\",\"params\": {\"detail_type\":\"private\",\"user_id\":\"123456\",\"message\":[{\"type\"=\"text\",\"data\": {\"text\":\"" + rec["candidates"][0]["content"]["parts"][0]["text"] + "\"}}]}}")
                sendMsg = {
    "action": "send_msg",
    "params": {
        "detail_type": "private",
        "user_id": msg["user_id"],  # 显式转换为字符串
        "message": [
            {
                "type": "text",  # 修正原代码中的 = 应为 :
                "data": {
                    "text": rec["candidates"][0]["content"]["parts"][0]["text"]
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
