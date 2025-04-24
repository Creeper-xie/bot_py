import sys
import json
import asyncio
import aiohttp
from collections import deque
from dataclasses import dataclass

from rich.console import Console
from websockets.asyncio.client import connect

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

console = Console()

MAX_HISTORY_LENGTH = 30
user_contents = {}

GENERATION_CONFIG = {
    "response_mime_type": "application/json",
    "response_schema": {
        "type": "object",
        "properties": {
            "logic": {
                "type": "string",
            },
            "status": {
                "type": "string",
                "enum": ["success", "skip"],
            },
            "messages": {
                "type": "array",
                "items": {
                    "type": "string",
                },
            },
        },
        "required": ["logic", "status", "messages"],
    },
} 


@dataclass
class Response:
    logic: str
    status: str
    messages: list[str]


async def ai(session, history) -> Response:
    tries=0
    global user_contents

    reqMsg={"system_instruction":{"parts":[{"text": prompt}]}, "contents" : list(history),"generationConfig": GENERATION_CONFIG}
    gemini_url= "{}?key={}".format(config["ai_url"],config["api_key"])
    while tries < 6:
        try:
            async with session.post(gemini_url, json=reqMsg) as resp:
                data = await resp.json()
        except aiohttp.ClientError:
            await asyncio.sleep(1)
            tries += 1
        else:
            console.log(data)
            if "candidates" not in data:
                raise Exception("喵")
            respText=data["candidates"][0]["content"]["parts"][0]["text"]
            resp = json.loads(respText)
            return Response(**resp)


async def client():
    uri=config["bot_ws_uri"]
    global user_contents
    async with aiohttp.ClientSession(trust_env=True) as session, \
               connect(uri,additional_headers={"Authorization": "Bearer {}".format(config["token"])}) as websocket:
        while True:
            msg = json.loads(await websocket.recv())
            if  "message_type" in msg and msg["message_type"] == "private" and msg["message"][0]["type"] == "text":
                console.log(msg)
                user_id = msg["user_id"]
                history=user_contents.setdefault(user_id, deque(maxlen=MAX_HISTORY_LENGTH))
                history.append({"role":"user","parts" : [{"text": msg["sender"]["nickname"] + "：" + msg["message"][0]["data"]["text"]}]})
                resp = await ai(session, history)
                if resp.status == "skip":
                    print("跳过这次回复")
                    continue
                history.append({"role":"model","parts" : [{"text": resp}]})
                for message in resp.messages:
                    sendMsg = {
    "action": "send_msg",
    "params": {
        "detail_type": "private",
        "user_id": msg["user_id"],
        "message": [
            {
                "type": "text",
                "data": {
                    "text": message
                }
            }
        ]
    }
}
                    await websocket.send(json.dumps(sendMsg))
                    await asyncio.sleep(config["break_time"])



if __name__ == "__main__":
    with open("config.toml", "rb") as f:
        config = tomllib.load(f)
    with open(config["prompt"], "r", encoding="utf-8") as f:
        prompt = f.read()
    asyncio.run(client())
