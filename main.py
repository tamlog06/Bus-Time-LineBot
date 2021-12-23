from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, FollowEvent,
)

import os
import requests
from bs4 import BeautifulSoup
import time
import re
app = Flask(__name__)

#環境変数取得
# LINE Developersで設定されているアクセストークンとChannel Secretを取得し、設定します。
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

class Text:
    def __init__(self):
        self.url_error = 'URLが正しくありません。\nポケロケのサイトから目的のバス停のバス接近情報を表示するURLを入力してください。\n詳しい使い方は〜を参照してください。\nhttp://blsetup.city.kyoto.jp/blsp/'
        self.start = '一番近いバスの接近状況を通知します。\n15分経過で自動終了します。'
        self.end = {'flag': '終了します。', 'time': '15分が経過したので終了します。', 'arrive': 'バスが到着したので終了します。'}
        self.bus = {'1': '1駅前をバスが通過しました。\nもうすぐ到着します。', '2': '2駅前をバスが通過しました。', '3': '3駅前をバスが通過しました。', 'no': '近くにまだバスがいません。', 'arrive': 'バスが到着しました。'}
        self.follow = '友達追加ありがとう！\nポケロケのサイトから目的のバス停のバス接近情報を表示するURLを入力してもらうと、バス接近情報を通知します！\n詳しい使い方は〜を参照してね！\nhttp://blsetup.city.kyoto.jp/blsp/'

class User:
    def __init__(self):
        self.user_flags = {}
        self.url = {}
    
    def add_user(self, event):
        self.user_flags[event.source.user_id] = False
    
    def add_URL(self, event):
        self.url[event.source.user_id] = event.message.text
    
    def set_flag(self, event, flag):
        self.user_flags[event.source.user_id] = flag

users = User()
txt = Text()

#Webhookからのリクエストをチェック
@app.route("/callback", methods=['POST'])
def callback():
    # リクエストヘッダーから署名検証のための値を取得
    signature = request.headers['X-Line-Signature']

    # リクエストボディを取得
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 署名を検証し、問題なければhandleに定義されている関数を呼び出す
    try:
        handler.handle(body, signature)
    # 署名検証で失敗した場合、例外を出す
    except LineBotApiError as e:
        print("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            print("  %s: %s" % (m.property, m.message))
        print("\n")
    except InvalidSignatureError:
        abort(400)
    # handleの処理を終えればOK
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # ユーザーが終了メッセージを送った場合はフラグを立てて通知を終了する
    if event.message.text == "flag":
        users.set_flag(event, True)
        return
    
    # 正しいURLかどうかチェック
    if not check_error(event):
        return
    
    t = 0
    before_text = ''
    # 時間制限で終了したかどうかのフラグ
    finish_flag = False
    while t < 900:
        # ユーザークラスから、各ユーザーのフラグを取得
        try:
            flag = users.user_flags[event.source.user_id]
        except KeyError:
            users.add_user(event)
            flag = users.user_flags[event.source.user_id]
        
        if flag:
            break

        # busimgクラスのimgを取得
        response = requests.get(users.url[event.source.user_id])
        soup = BeautifulSoup(response.text, 'html.parser')
        imgs = soup.find_all('img', class_='busimg')
        text = ''
        bus_num = 0
        for i in range(len(imgs)):
            # now_appが1駅前、bus_imgが2、3駅前のときのもの
            if imgs[i].get('src') == './disp_image_sp/bus_now_app_img_sp.gif' or './disp_image_sp/bus_img_sp.gif':
                bus_num += 1
                if not text == '':
                    text = txt.bus[str(i+1)]
        
        if t == 0:
            bus_num_before = bus_num
        
        # textが更新されなければ、バスが近くにいない
        if text == '':
            text = txt.bus['no']
        
        # 前の通知が1駅前のもので、現在のバスの数が前のものより少なければ、バスが到着したと判断して終了
        if before_text == txt.bus[str(1)] and bus_num < bus_num_before:
            line_bot_api.push_message(
                event.source.user_id,
                TextSendMessage(text=txt.bus['arrive']))
            finish_flag = True
            break

        # 前のサイクルで通知した内容と状況が変われば通知する
        if text != before_text:
            line_bot_api.push_message(
                event.source.user_id,
                TextSendMessage(text=text))
        
        before_text = text
        time.sleep(10)
        t += 10
    
    # ユーザーがフラグを立てて終了した時
    if users.user_flags[event.source.user_id]:
        text = txt.end['flag']
    # バスが到着して終了した時
    elif finish_flag:
        text = txt.end['arrive']
    # 時間制限で終了した時
    else:
        text = txt.end['time']
    
    users.set_flag(event, False)
    line_bot_api.push_message(
        event.source.user_id,
        TextSendMessage(text=text))

@handler.add(FollowEvent)
def handle_follow(event):
    users.add_user(event)
    app.logger.info("Got Follow event:" + event.source.user_id)
    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text='Got follow event'))

def check_error(event):
    try:
        users.add_URL(event)
        response = requests.get(users.url[event.source.user_id])
        # ステータスコードが200以外ならエラー
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        imgs = soup.find_all('img', class_='busimg')
        title = soup.find('title')
        if title == None or title.text == [] or not len(imgs)==3:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=txt.url_error))
            return False

        title = re.findall('：.*：', title.text)[0][1:-1]
        text = f'{title}\n{txt.start}'
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=text))
        return True

    except requests.exceptions.MissingSchema or requests.exceptions.ConnectionError or requests.exceptions.HTTPError:
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=txt.url_error))
        return False

# ポート番号の設定
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)