# Bus-Time-LineBot
市バスの運行状況を教えてくれるLine bot

# 友達追加
以下のQRコードを読み込むか、友達検索でIDを、`@004hxuhx`と検索すれば追加できます。

![image](https://github.com/tamlog06/Bus-Time-LineBot/assets/58413654/c846ba6e-3888-4582-8510-832941883970)


# How To Use
## ex.) 百万遍から京都駅に行きたい場合

## 1. 乗りたいバス停の名前を伝える。
Line botに、自分が乗りたい駅の名前を伝えてください。平仮名や、部分一致でも候補となるバス名を返答してくれます。勿論バス名を漢字で完全一致で伝えても返答してくれます。　
返ってきたURLをクリックして、ポケロケのサイトを開いてください。

![image](https://github.com/tamlog06/Bus-Time-LineBot/assets/58413654/aadab670-ba68-4757-88ec-f95439cd4b4c)

## 2. 候補となるバスの系統名を選択する。
自分の目的地に到達するバスの系統名を選択してください。今回の場合は、206番と17番が該当するので、これを選択して、下部の決定ボタンを押します。

![image](https://github.com/tamlog06/Bus-Time-LineBot/assets/58413654/13d6116d-09a0-405b-b225-9ef7a0bc8ad6)

## 3. 設定バス接近情報のURLを控える。
正しく設定ができていると、次のようなバス接近情報が確認できるサイトに飛ぶことができるはずです。このURLを控えておいてください。

![image](https://github.com/tamlog06/Bus-Time-LineBot/assets/58413654/1ceebf9c-6492-4506-8654-7f91a130bb27)

## 4. Line bot にURLを送信する。
先程控えたURLをLine botに送信してください。バス停まで３駅以内の距離にあるバスがある場合は、最も近いバスの系統名を随時教えてくれます。

![image](https://github.com/tamlog06/Bus-Time-LineBot/assets/58413654/41f5632d-ddb6-410d-9854-67c136010a7c)

## 5. 応答の終了
最初にURLを送ってから20分が経過するか、いずれかのバスが到着した場合に応答が終了します。バスに乗り過ごしてしまった場合などは再度同じURLを送ってください。
