from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage
)
import requests
from waitress import serve

app = Flask(__name__)
line_bot_api = LineBotApi('UoTKrw0p7aNjTjcxy4mhKn4fB8ckub8uojTEtUDmD+TiPl5Gzs7e5qPaCBEFEgG5fILPue9HeiYc5OEhAnL8pjLQMGwtYqCF/8XUtSoFlg9zFyxbhobtamezlBjnPhyBWfYzWjNyh+M6nGpWgpDmDgdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('a42f467a09899053c37f640cd7e748cb')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    if user_message == "一般車位":
        response = requests.get('https://script.google.com/macros/s/AKfycby17RLGiuSu_gPrytoVJ4slyw-UN8IfQukNUibockqrt1aNbIEe0Q9EaosFhiVu5t4UFQ/exec')
        data = response.json()
        if data['status'] == 'success':
            last_record = data['data']
            remaining_slots = last_record[0][2]
            reply_message = f"一般車位剩餘:{remaining_slots}個空位"
        else:
            reply_message = "無法獲取數據。"
    elif user_message == "殘障車位":
        response = requests.get('https://script.google.com/macros/s/AKfycbyACubqb08lPxc2uwDD9EjzhzJEq5s0jpCI1RrEMNLTXzLIWGY_y-7B7NeScjtVfFF0Sw/exec')
        data = response.json()
        if data['status'] == 'success':
            last_record = data['data']
            remaining_slots = last_record[0][2]
            reply_message = f"殘障車位剩餘:{remaining_slots}個空位"
        else:
            reply_message = "無法獲取數據。"
    elif user_message == "電動車位":
        response = requests.get('https://script.google.com/macros/s/AKfycbyBxpedTwB0VP8063IUvKxGdo-sB4L1Et-NahYPDCkXO9Hna1tzZbPfAGOecZFLdDdx/exec')
        data = response.json()
        if data['status'] == 'success':
            last_record = data['data']
            remaining_slots = last_record[0][2]
            reply_message = f"電動車位剩餘:{remaining_slots}個空位"
        else:
            reply_message = "無法獲取數據。"
    elif user_message == "機車車位":
        response = requests.get('https://script.google.com/macros/s/AKfycbwXwGzAn8wznt9eIYqa5n9-6WGpMiaHTFYUn8Y8yZYTf2O3zAsPVSUEw8mZrypv5bCxMw/exec')
        data = response.json()
        if data['status'] == 'success':
            last_record = data['data']
            remaining_slots = last_record[0][2]
            reply_message = f"機車車位剩餘:{remaining_slots}個空位"
        else:
            reply_message = "無法獲取數據。"
    else:
        reply_message = "1.請回答您想查詢的車位：、一般車位、殘障車位、電動車位、機車車位。2.舉報違規車輛流程：先輸入舉報車輛-->等待機器人回覆收到-->收到後接著上傳圖片及原因(兩者都要)-->機器人會回覆已通報工作人員感謝您!。"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_message)
    )

if __name__ == "__main__":
    serve(app, host='0.0.0.0', port=3000)
