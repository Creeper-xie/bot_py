import sys
import json
import asyncio
import aiohttp

from websockets.asyncio.client import connect


if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


MAX_HISTORY_LENGTH = 30
user_contents = {}
async def ai(session, history):
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
    while tries < 6:
        try:
            async with session.post(gemini_url, json=reqMsg) as resp:
                data = await resp.json()
        except aiohttp.ClientError:
            await asyncio.sleep(1)
            tries += 1
        else:
            print(data)
            if "candidates" not in data:
                raise Exception("喵")
            respText=data["candidates"][0]["content"]["parts"][0]["text"]
            return respText
async def client():
    uri=config["bot_ws_uri"]
    global user_contents
    async with aiohttp.ClientSession(trust_env=True) as session, \
               connect(uri,additional_headers={"Authorization": "Bearer {}".format(config["token"])}) as websocket:
        while True:
            msg = json.loads(await websocket.recv())
            if  "message_type" in msg and msg["message_type"] == "private" and msg["message"][0]["type"] == "text":
                print(msg)
                user_id = msg["user_id"]
                history=user_contents.setdefault(user_id, [])
                history.append({"role":"user","parts" : [{"text": msg["sender"]["nickname"] + "：" + msg["message"][0]["data"]["text"]}]})
                rec = await ai(session, history)
                if rec == "error":
                    continue
                history.append({"role":"model","parts" : [{"text": rec}]})
                history=history[-MAX_HISTORY_LENGTH:]
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
                    await asyncio.sleep(config["break_time"])



if __name__ == "__main__":
    with open("config.toml", "rb") as f:
        config = tomllib.load(f)
    with open(config["prompt"], "r", encoding="utf-8") as f:
        prompt = f.read()
    asyncio.run(client())
