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
import pickle
app = Flask(__name__)

#環境変数取得
# LINE Developersで設定されているアクセストークンとChannel Secretを取得し、設定します。
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

class Text:
    def __init__(self):
        self.error = {'url': 'URLが正しくありません。\nポケロケのサイトから目的のバス停のバス接近情報を表示するURLを入力してください。\n詳しい使い方は〜を参照してください。\nhttp://blsetup.city.kyoto.jp/blsp/',\
            'imgs': '表示するバスが複数選択されてしまっています。\n表示するバスは1つだけ選択してください。', 'no_url': 'URLが設定されていません。\nポケロケのサイトから目的のバス停のバス接近情報を表示するURLを入力してください。\n詳しい使い方は〜を参照してください。\nhttp://blsetup.city.kyoto.jp/blsp/'}
        self.start = '一番近いバスの接近状況を通知します。\n15分経過で自動終了します。'
        self.end = {'quit_flag': '終了します。', 'time': '15分が経過したので終了します。', 'arrive': 'バスが到着したので終了します。'}
        self.bus = {'1': '1駅前をバスが通過しました。\nもうすぐ到着します。', '2': '2駅前をバスが通過しました。', '3': '3駅前をバスが通過しました。', 'no': '近くにまだバスがいません。', 'arrive': 'バスが到着しました。'}
        self.follow = '友達追加ありがとうございます！\nポケロケのサイトから目的のバス停のバス接近情報を表示するURLを入力してもらうと、バス接近情報を通知します。\n詳しい使い方は〜を参照してください。\nhttp://blsetup.city.kyoto.jp/blsp/'

class User:
    def __init__(self):
        self.quit_flags = {}
        self.run_flags = {}
        self.url = {}
    
    def add_user(self, event):
        self.quit_flags[event.source.user_id] = False
        self.run_flags[event.source.user_id] = False
    
    def add_URL(self, event):
        self.url[event.source.user_id] = event.message.text
    
    def set_quit_flag(self, event, flag):
        self.quit_flags[event.source.user_id] = flag

    def set_run_flag(self, event, flag):
        self.run_flags[event.source.user_id] = flag

users = User()
txt = Text()

# 各バス停のバス停番号を辞書方で保存したもの
with open('station.pkl', 'rb') as f:
    station = pickle.load(f)

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
    if event.message.text == "終了":
        users.set_quit_flag(event, True)
        return

    # 起動中であれば何もしない
    try:
        run_flag = users.run_flags[event.source.user_id]
    except KeyError:
        users.add_user(event)
        run_flag = users.run_flags[event.source.user_id]
    
    if run_flag:
        return
    
    # 既にURLが設定されている場合は、そのURLを使用する
    if event.message.text == '開始':
        # 開始メッセージが送られてきたのにURLが設定されていない場合
        if not event.source.user_id in users.url:
            line_bot_api.reply_message(
                event.reply_token, 
                TextSendMessage(text=txt.error['no_url']))
            return
    
    # ユーザーがバス停の名前を送ってきた場合は、対応するURLを送信する
    elif not event.message.text.startswith('http'):
        text = event.message.text
        if text in station.keys():
            station_id = station[text]
            url = f'http://blsetup.city.kyoto.jp/blsp/step3.php?id={station_id}'
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=url)
            )
        else:
            # バス停名が見つからない場合は、近そうなものを探す（上限5個）
            candidates = candidate_names(text)
            if len(candidates) == 0:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text='そんなバス停ないよ')
                )
            elif len(candidates) == 1:
                station_id = station[candidates[0]]
                url = f'http://blsetup.city.kyoto.jp/blsp/step3.php?id={station_id}'
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=url)
                )
            else:
                text = f'どれ？\n{candidates}'
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=text)
                )
        return


    # 正しいURLかどうかチェック
    elif not check_error(event):
        return
    
    users.set_run_flag(event, True)
    users.set_quit_flag(event, False)
    response = requests.get(users.url[event.source.user_id])
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find('title')
    title = re.findall('：.*：', title.text)[0][1:-1]
    text = f'{title}\n{txt.start}'
    line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=text))
    t = 0
    before_text = ''
    # 時間制限で終了したかどうかのフラグ
    finish_flag = False
    while t < 900:
        # ユーザークラスから、各ユーザーのフラグを取得
        try:
            quit_flag = users.quit_flags[event.source.user_id]
        except KeyError:
            users.add_user(event)
            quit_flag = users.quit_flags[event.source.user_id]
        
        if quit_flag:
            break

        # busimgクラスのimgを取得
        response = requests.get(users.url[event.source.user_id])
        soup = BeautifulSoup(response.text, 'html.parser')
        imgs = soup.find_all('img', class_='busimg')
        text = ''
        bus_num = 0
        for i in range(len(imgs)):
            # now_appが1駅前、bus_imgが2、3駅前のときのもの
            if imgs[i].get('src') == './disp_image_sp/bus_now_app_img_sp.gif':
                bus_num += 1
                if text == '':
                    text = txt.bus['1']
            elif  imgs[i].get('src') ==  './disp_image_sp/bus_img_sp.gif':
                bus_num += 1
                if text == '':
                    text = txt.bus[str(i+1)]
        
        if t == 0:
            bus_num_before = bus_num
        
        # textが更新されなければ、バスが近くにいない
        if text == '':
            text = txt.bus['no']
        
        # 前の通知が1駅前のもので、現在のバスの数が前のものより少なければ、バスが到着したと判断して終了
        if before_text == txt.bus['1'] and (bus_num < bus_num_before or text != txt.bus['1']):
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
    if users.quit_flags[event.source.user_id]:
        text = txt.end['quit_flag']
    # バスが到着して終了した時
    elif finish_flag:
        text = txt.end['arrive']
    # 時間制限で終了した時
    else:
        text = txt.end['time']
    
    users.set_quit_flag(event, False)
    users.set_run_flag(event, False)
    line_bot_api.push_message(
        event.source.user_id,
        TextSendMessage(text=text))

@handler.add(FollowEvent)
def handle_follow(event):
    users.add_user(event)
    app.logger.info("Got Follow event:" + event.source.user_id)
    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text=txt.follow))

def check_error(event):
    try:
        response = requests.get(event.message.text)

        # ステータスコードが200以外ならエラー
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        imgs = soup.find_all('img', class_='busimg')
        title = soup.find('title')
        if len(imgs) > 3:
            line_bot_api.push_message(
                event.source.user_id,
                TextSendMessage(text=txt.error['imgs']))
            return False
        if title == None or title.text == [] or len(imgs) < 3:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(ext=txt.error['url']))
            return False
        
        users.add_URL(event)
        return True

    except requests.exceptions.MissingSchema or requests.exceptions.ConnectionError or requests.exceptions.HTTPError:
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=txt.error['url']))
        return False

def candidate_names(name):
    candidate_names = []
    for key in station.keys():
        if name in key:
            candidate_names.append(key)
        
        if len(candidate_names) >= 5:
            return candidate_names
    
    return candidate_names


# ポート番号の設定
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)