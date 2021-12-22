# import requests

# response = requests.get('http://test.neet-ai.com')
# print(response.text)

import requests
from bs4 import BeautifulSoup
import re

# response = requests.get('http://tdoc.info/beautifulsoup/#the-parse-tree')
# soup = BeautifulSoup(response.text,'html.parser')

# title = soup.title.string
# print(title)

# link = soup.a.get('href')
# print(link)

# links = soup.find_all('a')
# for link in links:
#     print(link.get('href'))

# twitter = soup.find('a', id='twitter').get('href')
# twitter = soup.find('a', class_='twitter').get('href')

# print(twitter)
class Text:
    def __init__(self):
        self.start = '一番近いバスの接近状況を通知します。\n10分経過で自動終了します。'
        self.url_error = 'URLが正しくありません。\nポケロケのサイトから目的のバス停のバス接近情報を表示するURLを入力してください。\n詳しい使い方は〜を参照してください。\nhttp://blsetup.city.kyoto.jp/blsp/'
        self.bus = {'1': '1駅前をバスが通過しました。\nもうすぐ到着します。', '2': '2駅前をバスが通過しました。', '3': '3駅前をバスが通過しました。'}
        self.follow = '友達追加ありがとう！\nポケロケのサイトから目的のバス停のバス接近情報を表示するURLを入力してもらうと、バス接近情報を通知します！\n詳しい使い方は〜を参照してね！\nhttp://blsetup.city.kyoto.jp/blsp/'


text = Text()
print(text.bus['1'])
# print(text.follow)

response = requests.get('http://blsetup.city.kyoto.jp/blsp/show.php?sid=d21b741ff8826d8b0fb6063e148dcdf3')
# response = requests.get('http://blsetup.city.kyoto.jp/blsp/show.php?sid=0cc1cc39e02d7f1e490b00e34a0e1eaaaa')
soup = BeautifulSoup(response.text,'html.parser')
imgs = soup.find_all('img', class_='busimg')
title = soup.find('title').text
print(imgs)
print()
print(title)
print()
t = re.findall('：.*：', title)[0][1:-1]
print(t)
print()
print(len(imgs))
# imgs_bus = soup.find_all('img', src="./disp_image_sp/bus_img_sp.gif")
# imgs = soup.find_all('img', src="./disp_image_sp/bus_now_app_img_sp.gif")
# for i in range(len(imgs)):
#     print(imgs[i].get('src'))
#     print(imgs[i].get('src') == './disp_image_sp/not_bus_img_sp.gif')


for i in range(len(imgs)):
    if imgs[i].get('src') == './disp_image_sp/bus_now_app_img_sp.gif':
        text = f'{i+1}駅前を過ぎました。もうすぐ到着します。'
        print(text)
        break
    if imgs[i].get('src') == './disp_image_sp/bus_img_sp.gif':
        text = f'{i+1}駅前をバスが過ぎました。'
        print(text)
        break