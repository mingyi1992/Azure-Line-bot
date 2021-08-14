from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
import os
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    FlexSendMessage
)
import json
import time
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.face.models import TrainingStatusType, Person
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes,VisualFeatureTypes


app = Flask(__name__)

# 電腦視覺
SUBSCRIPTION_KEY = os.getenv("Subscription_key")
ENDPOINT = os.getenv("subscription_endpoint")
CV_CLIENT = ComputerVisionClient(
    ENDPOINT, CognitiveServicesCredentials(SUBSCRIPTION_KEY))

# 人臉
FACE_KEY = os.getenv("Face_key")
FACE_END = os.getenv("Face_endpoint")
FACE_CLIENT = FaceClient(
  FACE_END, CognitiveServicesCredentials(FACE_KEY))
PERSON_GROUP_ID = "cv"

# LINE Messaging API
LINE_SECRET = os.getenv("Line_secret")
LINE_TOKEN = os.getenv("Line_token")
LINE_BOT = LineBotApi(LINE_TOKEN)
HANDLER = WebhookHandler(LINE_SECRET)

# imgur API
IMGUR_CONFIG = {
  "client_id": os.getenv("Client_id"),
  "client_secret": os.getenv("Client_secret"),
  "access_token": os.getenv("Access_token"),
  "refresh_token": os.getenv("Refresh_token")
}
IMGUR_CLIENT = Imgur(config=IMGUR_CONFIG)

@app.route("/")
def hello():
    "hello world"
    return "Hello World!!!!!"


#@app.route("/callback", methods=["POST"])
#def callback():
    # X-Line-Signature: 數位簽章
#    signature = request.headers["X-Line-Signature"]
#    print(signature)
#    body = request.get_data(as_text=True)
#    print(body)
#    try:
#        HANDLER.handle(body, signature)
#    except InvalidSignatureError:
#        print("Check the channel secret/access token.")
#        abort(400)
#    return "OK"

# message 可以針對收到的訊息種類
#@HANDLER.add(MessageEvent, message=TextMessage)
#def handle_message(event):
#    if event.message.text.upper()=='COFFEE':
#        with open("coffee.json", "r") as f_r:
#            bubble = json.load(f_r)
#        f_r.close()
    # 依情況更動 components
#        LINE_BOT.reply_message(
#                event.reply_token,
#            [FlexSendMessage(alt_text="Report", contents=bubble)]
#        )   
#    else:
#        url_dict = {
#            "GOOGLE":"https://www.google.com.tw/?hl=zh_TW",
#            "HELP":"https://developers.line.biz/zh-hant/docs/messaging-api/"}
# 將要發出去的文字變成TextSendMessage
#        try:
#            url = url_dict[event.message.text.upper()]
#            message = TextSendMessage(text=url)
#        except:
#            message = TextSendMessage(text=event.message.text)
# 回覆訊息
#    LINE_BOT.reply_message(event.reply_token, message)
