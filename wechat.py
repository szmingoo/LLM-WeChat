from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import hashlib
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
import httpx
from typing import Dict, Any,Optional
import time
app = FastAPI()

async def get_llm(query: str) -> str:
    timeout_seconds = 10  # 设置超时时间为10秒，根据实际情况调整
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout_seconds)) as client:
        url = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation'
        headers = {
            'Authorization': 'Bearer sk-52b96574fc1949a380590eabc9403e30',
            'Content-Type': 'application/json'
        }
        data: Dict[str, Any] = {
            "model": "qwen-plus",
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
        try:
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()
            answer = response.json()["output"]["text"]
        except httpx.TimeoutException as e:
            print(f"请求超时: {e}")
            # 根据需求处理超时情况，比如返回特定的错误信息或者重试
            answer = "请求超时，请稍后再试。"
        except httpx.HTTPStatusError as e:
            print(f"HTTP错误: {e}")
            answer = "服务器错误，请稍后再试。"
        except Exception as e:
            print(f"发生错误: {e}")
            answer = "发生了未知错误。"
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
