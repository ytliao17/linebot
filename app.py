from flask import Flask, request, abort, render_template
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage, TextSendMessage
)
import requests
import psycopg2
from waitress import serve

app = Flask(__name__)

# LINE Bot 設定
line_bot_api = LineBotApi('UoTKrw0p7aNjTjcxy4mhKn4fB8ckub8uojTEtUDmD+TiPl5Gzs7e5qPaCBEFEgG5fILPue9HeiYc5OEhAnL8pjLQMGwtYqCF/8XUtSoFlg9zFyxbhobtamezlBjnPhyBWfYzWjNyh+M6nGpWgpDmDgdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('a42f467a09899053c37f640cd7e748cb')

# 暫存舉報資料
session_data = {}

# 資料庫設定
db_config = {
    'host': 'dpg-d1h8l56mcj7s73djpiu0-a',
    'user': 'park_user',
    'password': 'on0eDp2TKc9RrieojfVzOWpD2K6clg59',
    'database': 'park',
    'port': 5432
}

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
def handle_text(event):
    user_id = event.source.user_id
    user_message = event.message.text.strip()

    if user_message == "舉報車輛":
        session_data[user_id] = {"text": None, "image": None}
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請上傳違規車輛的照片（要有車牌）與原因（文字）！")
        )
        return

    if user_id in session_data:
        data = session_data[user_id]
        if data["text"] is None:
            session_data[user_id]["text"] = user_message
            check_report_complete(event, user_id)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請上傳違規車輛圖片（要有車牌）")
            )
        return

    # 車位查詢功能
    reply_message = handle_parking_query(user_message)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    user_id = event.source.user_id
    if user_id in session_data:
        data = session_data[user_id]
        if data["image"] is None:
            # 這裡先存「收到圖片」，你可以改存真實圖片URL
            session_data[user_id]["image"] = "收到圖片"
            check_report_complete(event, user_id)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請輸入文字說明")
            )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請先輸入「舉報車輛」以啟動回報流程。")
        )

def check_report_complete(event, user_id):
    data = session_data.get(user_id, {})
    if data.get("image") and data.get("text"):
        # 寫入MySQL
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reports (user_id, image_url, description) VALUES (%s, %s, %s)",
            (user_id, data["image"], data["text"])
        )
        conn.commit()
        conn.close()

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="已通報工作人員，感謝您的協助！")
        )
        del session_data[user_id]  # 清理暫存

def handle_parking_query(user_message):
    urls = {
        "一般車位": 'https://script.google.com/macros/s/AKfycby17RLGiuSu_gPrytoVJ4slyw-UN8IfQukNUibockqrt1aNbIEe0Q9EaosFhiVu5t4UFQ/exec',
        "殘障車位": 'https://script.google.com/macros/s/AKfycbyACubqb08lPxc2uwDD9EjzhzJEq5s0jpCI1RrEMNLTXzLIWGY_y-7B7NeScjtVfFF0Sw/exec',
        "電動車位": 'https://script.google.com/macros/s/AKfycbyBxpedTwB0VP8063IUvKxGdo-sB4L1Et-NahYPDCkXO9Hna1tzZbPfAGOecZFLdDdx/exec',
        "機車車位": 'https://script.google.com/macros/s/AKfycbwXwGzAn8wznt9eIYqa5n9-6WGpMiaHTFYUn8Y8yZYTf2O3zAsPVSUEw8mZrypv5bCxMw/exec'
    }
    if user_message in urls:
        url = urls[user_message]
        return fetch_parking_data(url, user_message)
    else:
        return (
            "1.請回答您想查詢的車位：一般車位、殘障車位、電動車位、機車車位。\n"
            "2.舉報違規車輛流程：輸入「舉報車輛」→ 等候提示 → 上傳圖片與原因 → 回覆確認。\n"
            "3.如有問題請撥打：(04)23924505 聯絡工作人員。"
        )

def fetch_parking_data(url, type_name):
    try:
        response = requests.get(url)
        data = response.json()
        if data['status'] == 'success':
            remaining = data['data'][0][2]
            return f"{type_name}剩餘:{remaining}個空位"
        else:
            return "無法獲取數據。"
    except:
        return "讀取資料錯誤，請稍後再試。"
@app.route("/reports")
def reports():
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT * FROM reports ORDER BY created_at DESC")
    data = cursor.fetchall()
    conn.close()
    return render_template("reports.html", reports=data)

if __name__ == "__main__":
    serve(app, host='0.0.0.0', port=3000)
