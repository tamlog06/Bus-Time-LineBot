# import requests

# response = requests.get('http://test.neet-ai.com')
# print(response.text)

import requests
from bs4 import BeautifulSoup

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

response = requests.get('http://blsetup.city.kyoto.jp/blsp/show.php?sid=d21b741ff8826d8b0fb6063e148dcdf3')
soup = BeautifulSoup(response.text,'html.parser')
imgs = soup.find_all('img', class_='busimg')
# imgs_bus = soup.find_all('img', src="./disp_image_sp/bus_img_sp.gif")
# imgs = soup.find_all('img', src="./disp_image_sp/bus_now_app_img_sp.gif")
for img in imgs:
    print(img['src'])
