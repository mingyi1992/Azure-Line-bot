from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
import os
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
)
import json

app = Flask(__name__)

LINE_SECRET = os.getenv("Line_secret")
LINE_TOKEN = os.getenv("Line_token")
LINE_BOT = LineBotApi(LINE_TOKEN)
HANDLER = WebhookHandler(LINE_SECRET)

@app.route("/")
def hello():
    "hello world"
    return "Hello World!!!!!"

@app.route("/callback", methods=["POST"])
def callback():
    # X-Line-Signature: 數位簽章
    signature = request.headers["X-Line-Signature"]
    print(signature)
    body = request.get_data(as_text=True)
    print(body)
    try:
        HANDLER.handle(body, signature)
    except InvalidSignatureError:
        print("Check the channel secret/access token.")
        abort(400)
    return "OK"

# message 可以針對收到的訊息種類
@HANDLER.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text.upper()=='COFFEE':
        with open("coffee.json", "r") as f_r:
            bubble = json.load(f_r)
        f_r.close()
    # 依情況更動 components
        LINE_BOT.reply_message(
                event.reply_token,
            [FlexSendMessage(alt_text="Report", contents=bubble)]
        )   
    else:
        url_dict = {
            "GOOGLE":"https://www.google.com.tw/?hl=zh_TW",
            "HELP":"https://developers.line.biz/zh-hant/docs/messaging-api/"}
# 將要發出去的文字變成TextSendMessage
        try:
            url = url_dict[event.message.text.upper()]
            message = TextSendMessage(text=url)
        except:
            message = TextSendMessage(text=event.message.text)
# 回覆訊息
    LINE_BOT.reply_message(event.reply_token, message)
