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
app = Flask(__name__)

#環境変数取得
# LINE Developersで設定されているアクセストークンとChannel Secretをを取得し、設定します。
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

class User:
    def __init__(self):
        self.users = {}
        self.user_flags = {}
        self.url = {}
    
    def add_user(self, event):
        self.users[event.source.user_id] = event.source.user_id
        self.user_flags[event.source.user_id] = False
    
    def add_URL(self, event):
        self.url[event.source.user_id] = event.message.text
    
    def set_flag(self, event):
        self.user_flags[event.source.user_id] = True

users = User()

## 1 ##
#Webhookからのリクエストをチェックします。
@app.route("/callback", methods=['POST'])
def callback():
    # リクエストヘッダーから署名検証のための値を取得します。
    signature = request.headers['X-Line-Signature']

    # リクエストボディを取得します。
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    # 署名を検証し、問題なければhandleに定義されている関数を呼び出す。
    try:
        handler.handle(body, signature)
    # 署名検証で失敗した場合、例外を出す。
    except LineBotApiError as e:
        print("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            print("  %s: %s" % (m.property, m.message))
        print("\n")
    except InvalidSignatureError:
        abort(400)
    # handleの処理を終えればOK
    return 'OK'

## 2 ##
###############################################
#LINEのメッセージの取得と返信内容の設定(オウム返し)
###############################################

#LINEでMessageEvent（普通のメッセージを送信された場合）が起こった場合に、
#def以下の関数を実行します。
#reply_messageの第一引数のevent.reply_tokenは、イベントの応答に用いるトークンです。 
#第二引数には、linebot.modelsに定義されている返信用のTextSendMessageオブジェクトを渡しています。

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # response = requests.get('http://blsetup.city.kyoto.jp/blsp/show.php?sid=d21b741ff8826d8b0fb6063e148dcdf3')

    if event.message.text == "flag":
        users.set_flag(event)
        flag = user.user_flags[event.source.user_id]
        line_bot_api.push_message(
                event.source.user_id,
                TextSendMessage(text=flag))
        return
    else:
        flag = users.user_flags[event.source.user_id]
        line_bot_api.push_message(
                event.source.user_id,
                TextSendMessage(text=flag))

    try:
        users.add_URL(event)
        request = requests.get(users.url[event.source.user_id])
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='10秒刻みで一番近いバスの状況を通知します。\n5分経過で終了します。'))
    except:
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='URLが間違っています。'))
        return
    
    start = time.time()
    t = 0
    before_text = ''
    while t < 300:
        if users.user_flags[event.source.user_id]:
            line_bot_api.push_message(
                event.source.user_id,
                TextSendMessage(text='flagで終了します。'))
            break

        # response = requests.get(event.message.text)
        response = requests.get(users.url[event.source.user_id])
        soup = BeautifulSoup(response.text, 'html.parser')
        imgs = soup.find_all('img', class_='busimg')
        # imgs_bus = soup.find_all('img', src="./disp_image_sp/bus_img_sp.gif")
        # imgs = soup.find_all('img', src="./disp_image_sp/bus_now_app_img_sp.gif")
        text = ''
        for i in range(len(imgs)):
            tx = imgs[i].get('src')
            line_bot_api.push_message(
                    event.source.user_id,
                    TextSendMessage(text=f'{tx}'))
        
        for i in range(len(imgs)):
            if imgs[i].get('src') == './disp_image_sp/bus_now_app_img_sp.gif':
                text = f'{i+1}駅前を過ぎました。もうすぐ到着します。'
                break
            if imgs[i].get('src') == './disp_image_sp/bus_img_sp.gif':
                text = f'{i+1}駅前をバスが過ぎました。'
                break
        if text == '':
            text = 'バスがまだ近くにいません。'
        if text != before_text:
            line_bot_api.push_message(
                event.source.user_id,
                TextSendMessage(text=text))
        # else:
        #     line_bot_api.push_message(
        #         event.source.user_id,
        #         TextSendMessage(text='同じ状況'))
        before_text = text
        time.sleep(10)
        t += 10
    
    line_bot_api.push_message(
        event.source.user_id,
        TextSendMessage(text='終了します。'))
    


        #     if i == 2:
        #         if img['src'] == './disp_image_sp/bus_now_app_img_sp.gif':
        #             text += f'{3-i}駅前にバスがいます。もうすぐ到着します。'
        #         else:
        #             text += f'{3-i}駅前にバスがいません。'
        #     if img['src'] != './disp_image_sp/not_bus_img_sp.gif':
        #         text += f'{3-i}駅前にバスがいます。\n'
        #     else:
        #         text += f'{3-i}駅前にバスがいません。\n'
        # # text = event.message.text + '\n' + text

        # # for i in range(5):
        #     # line_bot_api.reply_message(
        #     #     event.reply_token,
        #     #     TextSendMessage(text=text)) #ここでオウム返しのメッセージを返します。
        # line_bot_api.push_message(
        #     event.source.user_id,
        #     TextSendMessage(text=text)) #ここでオウム返しのメッセージを返します。

        # time.sleep(15)
        # t += 15

@handler.add(FollowEvent)
def handle_follow(event):
    users.add_user(event)
    app.logger.info("Got Follow event:" + event.source.user_id)
    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text='Got follow event'))


# ポート番号の設定
# https://bus-time-information.herokuapp.com/callback
if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)