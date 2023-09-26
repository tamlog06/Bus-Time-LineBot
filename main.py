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
        self.error = {'url': 'URL間違ってるで。\n以下のURLから操作方法を確認してな。\nhttps://github.com/tamlog06/Bus-Time-LineBot',\
            'no_url': 'URLが設定されてないで。\n以下のURLから操作方法を確認してな。\nhttps://github.com/tamlog06/Bus-Time-LineBot',\
            'no_bus_stop': 'そんなバス停ないで。\n以下のURLから操作方法を確認してな。\nhttps://github.com/tamlog06/Bus-Time-LineBot',\
            'starting': '既に起動中やで。他の設定にしたいんやったら、「終了」って入力してからまた新しく登録し直してくれや。'}
        self.start = '一番近いバスの接近状況を通知するで。\n20分経過で自動終了するしな。'
        self.end = {'quit_flag': '終了するで。ほな。', 'time': '20分が経過したから終了するで。', 'arrive': 'バスが到着したし終了するな。'}
        self.bus = {1: '1駅前を以下のバスが通過したで。\nもうすぐ到着するで。\n急いでや。', 2: '2駅前を以下のバスが通過したで。', 3: '3駅前を以下のバスが通過したで。', 4: '近くにまだバスおらんで。', 'arrive': 'バスが到着したわ。\nちゃんと乗れたか？'}
        self.follow = '友達追加ありがとう！\n以下のURLから操作方法を確認してな。\nhttps://github.com/tamlog06/Bus-Time-LineBot'
    
    def return_bus_text(self, bus_id, keitoList):
        assert type(bus_id) == int
        if bus_id == 4:
            return self.bus[bus_id]
        else:
            keito = '\n'.join(keitoList)
            return f'{self.bus[bus_id]}\n{keito}'

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

userClass = User()
textClass = Text()

# 各バス停のバス停番号を辞書方で保存したもの
with open('station.pkl', 'rb') as f:
    stationDict = pickle.load(f)

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
        userClass.set_quit_flag(event, True)
        return

    # 起動中かどうかのフラグ
    try:
        run_flag = userClass.run_flags[event.source.user_id]
    except KeyError:
        userClass.add_user(event)
        run_flag = userClass.run_flags[event.source.user_id]
    
    # 起動中であればエラーを返す
    if run_flag:
        line_bot_api.reply_message(
            event.reply_token, 
            TextSendMessage(text=textClass.error['starting'])
        )
        return
    
    # 既にURLが設定されている場合は、そのURLを使用する
    if event.message.text == '開始':
        # 開始メッセージが送られてきたのにURLが設定されていない場合
        if not event.source.user_id in userClass.url:
            line_bot_api.reply_message(
                event.reply_token, 
                TextSendMessage(text=textClass.error['no_url'])
            )
            return
    
    # ユーザーがバス停のリンク以外を送った場合
    elif not event.message.text.startswith('http'):
        text = event.message.text
        # 正しいバス停の名前が送られてきた場合
        if text in stationDict.keys():
            station_id = stationDict[text]
            url = f'http://blsetup.city.kyoto.jp/blsp/step3.php?id={station_id}'
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=url)
            )
            return
        
        # バス停名が見つからない場合は、近そうなものを探す（上限5個）
        candidates = candidate_names(text)
        # 一致するものがない場合
        if len(candidates) == 0:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=textClass.error['no_bus_stop'])
            )
            return
        elif len(candidates) == 1:
            station_id = stationDict[candidates[0]]
            url = f'http://blsetup.city.kyoto.jp/blsp/step3.php?id={station_id}'
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=url)
            )
            return
        else:
            candidates = '\n'.join(candidates)
            text = f'この中にある？\n{candidates}'
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=text)
            )
            return

    # 正しいURLかどうかチェック
    elif not check_error(event):
        return
    
    # 開始処理
    userClass.set_run_flag(event, True)
    userClass.set_quit_flag(event, False)
    response = requests.get(userClass.url[event.source.user_id])
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find('title')
    title = re.findall('：.*：', title.text)[0][1:-1]
    text = f'{title}\n{textClass.start}'
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=text)
    )
    
    start_time = time.time()
    now = start_time
    before_message = ''
    before_message_id = -1
    before_nbus = -1
    before_keitoList = []
    # バスが来たかどうかのフラグ
    arrive_flag = False

    # 20分間
    while now - start_time < 1200:
        # ユーザークラスから、各ユーザーのフラグを取得
        try:
            quit_flag = userClass.quit_flags[event.source.user_id]
        except KeyError:
            userClass.add_user(event)
            quit_flag = userClass.quit_flags[event.source.user_id]
        
        if quit_flag:
            break

        # bls-keito-num-imgクラス（バスの系統の取得）とbusimgクラス（バスが存在するかどうかの判定）のimgを取得
        response = requests.get(userClass.url[event.source.user_id])
        soup = BeautifulSoup(response.text, 'html.parser')
        imgs = soup.find_all('img', class_=['bls-keito-num-img', 'busimg'])

        nbus = 0
        text_id = 4
        keitoList = []
        
        for i, img in enumerate(imgs):
            # 系統情報
            if i % 4 == 0:
                keito = img.get('alt')
            # バスが来ているかどうかの情報
            else:
                # バスが来ている場合
                if img.get('src') == "./disp_image_sp/bus_now_app_img_sp.gif" or img.get('src') == './disp_image_sp/bus_img_sp.gif':
                    # 今まで見た中で最も近いものと距離が同じ場合
                    if text_id == i%4:
                        keitoList.append(keito)
                    # 今まで見た中で最も近いものより距離が近い場合
                    elif text_id > i%4:
                        text_id = i%4
                        keitoList = [keito]
                    nbus += 1
        
        # 送るメッセージ
        message = textClass.return_bus_text(text_id, keitoList)
        
        # 前の通知が1駅前のもので、現在のバスの数が前のものより少ないか、一番近いバスが２駅前になったか、一番近いバスの系統の数が少なくなったら、バスが到着したと判定して終了
        if before_message_id == 1 and (nbus < before_nbus or text_id != 1 or len(keitoList) < len(before_keitoList)):
            line_bot_api.push_message(
                event.source.user_id,
                TextSendMessage(text=textClass.bus['arrive']))
            arrive_flag = True
            break

        # 前のサイクルで通知した内容と状況が変われば通知する
        if message != before_message:
            line_bot_api.push_message(
                event.source.user_id,
                TextSendMessage(text=message))
        
        before_message = message
        before_message_id = text_id
        before_nbus = nbus
        before_keitoList = keitoList

        # アクセス負荷を下げるため10秒待つ
        time.sleep(10)

        now = time.time()
    
    # ユーザーがフラグを立てて終了した時
    if userClass.quit_flags[event.source.user_id]:
        message = textClass.end['quit_flag']
    # バスが到着して終了した時
    elif arrive_flag:
        message = textClass.end['arrive']
    # 時間制限で終了した時
    else:
        message = textClass.end['time']
    
    userClass.set_quit_flag(event, False)
    userClass.set_run_flag(event, False)
    line_bot_api.push_message(
        event.source.user_id,
        TextSendMessage(text=message)
    )
    return

@handler.add(FollowEvent)
def handle_follow(event):
    userClass.add_user(event)
    app.logger.info("Got Follow event:" + event.source.user_id)
    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text=textClass.follow))

def check_error(event):
    try:
        response = requests.get(event.message.text)

        # ステータスコードが200以外ならエラー
        response.raise_for_status()

        # busimgクラスのimgを取ってくる
        soup = BeautifulSoup(response.text, 'html.parser')
        imgs = soup.find_all('img', class_='busimg')
        title = soup.find('title')

        # 正しく設定されていれば、画像の数は3個以上になるはず
        if title == None or title.text == [] or len(imgs) < 3:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(ext=textClass.error['url']))
            return False
        
        # 問題なければurlを割り当ててTrueを返す
        userClass.add_URL(event)
        return True

    except requests.exceptions.MissingSchema or requests.exceptions.ConnectionError or requests.exceptions.HTTPError:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=textClass.error['url'])
        )
        return False

# 近い名前のバス停を5個まで探索する
def candidate_names(name):
    candidate_names = []
    for key in stationDict.keys():
        if name in key:
            candidate_names.append(key)
        
        if len(candidate_names) >= 5:
            return candidate_names
    
    return candidate_names

# ポート番号の設定
if __name__ == "__main__":
    from waitress import serve
    port = int(os.getenv("PORT", 5000))
    # app.run(host="0.0.0.0", port=port)
    serve(app, host="0.0.0.0", port=port)
