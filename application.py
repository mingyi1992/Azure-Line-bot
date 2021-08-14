from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
import os
from linebot.models import (
    MessageEvent,
    TextMessage,
    ImageMessage,
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
from imgur_python import Imgur
from datetime import datetime, timezone, timedelta


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


@app.route("/callback", methods=["POST"])
def callback():
    # X-Line-Signature:  數位簽章
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

def azure_face_recognition(filename):
    img = open(filename, "r+b")
    detected_face = FACE_CLIENT.face.detect_with_stream(
        img, detection_model="detection_01"
    )
    # 多於一張臉的情況
    if len(detected_face) != 1:
        return ""
    results = FACE_CLIENT.face.identify(
      [detected_face[0].face_id], PERSON_GROUP_ID)
    # 沒有結果的情況
    if len(results) == 0:
        return "unknown"
    result = results[0].as_dict()
    # 找不到相像的人
    if len(result["candidates"]) == 0:
        return "unknown"
    # 雖然有類似的人，但信心程度太低
    if result["candidates"][0]["confidence"] < 0.6:
        return "unknown"
    person = FACE_CLIENT.person_group_person.get(
        PERSON_GROUP_ID, result["candidates"][0]["person_id"]
    )
    return person.name

@HANDLER.add(MessageEvent, message=ImageMessage)
def handle_content_message(event):
    # 先把傳來的照片存檔
    filename = "{}.jpg".format(event.message.id)
    message_content = LINE_BOT.get_message_content(
      event.message.id)
    with open(filename, "wb") as f_w:
        for chunk in message_content.iter_content():
            f_w.write(chunk)
    f_w.close()

    # 將取得照片的網路連結
    image = IMGUR_CLIENT.image_upload(filename, "", "")
    link = image["response"]["data"]["link"]
    name = azure_face_recognition(filename)
    if name != "": # 如果只有一張人臉，輸出人臉辨識結果
        now = datetime.now(timezone(timedelta(hours=8))).\
        strftime("%Y-%m-%d %H:%M") # 注意時區
        output = "{0}, {1}".format(name, now)
    else:
        plate = azure_ocr(link)
        link_ob = azure_object_detection(link, filename)
# 分別影像連結和偵測結果放到Flex Message
    with open("detect_result.json", "r") as f_r:
        bubble = json.load(f_r)
    f_r.close()
    bubble["body"]["contents"][0]["contents"][0]["contents"][0]["text"] = output
    bubble["header"]["contents"][0]["contents"][0]["contents"][0]["url"] = link
    LINE_BOT.reply_message(
        event.reply_token, 
        [FlexSendMessage(alt_text="Report", contents=bubble)]
    )


# message 可以針對收到的訊息種類
@HANDLER.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text.upper()=='COFFEE':
        with open("coffee.json", "r") as f_r:
            bubble = json.load(f_r)
        f_r.close()
#    依情況更動 components
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
