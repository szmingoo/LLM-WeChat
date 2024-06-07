from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import hashlib
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
from typing import Optional
import time
app = FastAPI()
import asyncio

import httpx
from typing import Dict, Any

async def get_llm(query: str) -> str:
    async with httpx.AsyncClient() as client:
        url = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation'
        headers = {
            'Authorization': 'Bearer ',#输入你的千问key
            'Content-Type': 'application/json'
        }
        data: Dict[str, Any] = {
            "model": "qwen-turbo",
            "input": {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant."
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ]
            },
        }
        response = await client.post(url, json=data, headers=headers)
        response.raise_for_status()  # 这会抛出异常，如果响应状态码不是200
        answer = response.json()["output"]["text"]
        return answer
@app.get("/")
async def root(request: Request):
    query_params = request.query_params
    signature = query_params.get("signature")
    token = "shenzhiming"
    echostr = query_params.get("echostr")
    timestamp = query_params.get("timestamp")
    nonce = query_params.get("nonce")
    params = [token, timestamp, nonce]
    params.sort()
    _signature = hashlib.sha1("".join(params).encode("utf-8")).hexdigest()
    if _signature == signature:
        return PlainTextResponse(echostr)
    else:
        return PlainTextResponse("Invalid signature", status_code=403)
@app.post("/")
async def handle_post(request: Request):
    try:
        body = await request.body()
        xml_tree = ET.fromstring(body)
        ToUserName = xml_tree.find(".//ToUserName")
        FromUserName = xml_tree.find(".//FromUserName")
        MsgType = xml_tree.find(".//MsgType")
        if MsgType is not None and MsgType.text == "text":
            Content = xml_tree.find(".//Content")
            if Content is not None:
                content = Content.text
                # print(content)
                llm_answer=await get_llm(content)
                createTimeSec = int(time.time())
                reply_xml = (
                    f"<xml>"
                    f"<ToUserName><![CDATA[{FromUserName.text}]]></ToUserName>"
                    f"<FromUserName><![CDATA[{ToUserName.text}]]></FromUserName>"
                    f"<CreateTime>{createTimeSec}</CreateTime>"
                    f"<MsgType><![CDATA[text]]></MsgType>"
                    f"<Content><![CDATA[{llm_answer}]]></Content>"
                    f"</xml>"
                )
                return PlainTextResponse(reply_xml, media_type="application/xml")
            else:
                return PlainTextResponse("", status_code=200)
        else:
            return PlainTextResponse("", status_code=200)
    except ParseError:
        return PlainTextResponse("Invalid XML format", status_code=400)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
