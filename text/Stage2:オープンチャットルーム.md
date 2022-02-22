# オープンチャットルーム

Stage1では外部APIを使ってチャットbotとチャットできるものを作りました。

今回はシンプルなチャットルームを作って行きたいと思います。

Stage1ではHTTPリクエストをサーバに送っているですが、残念ながらその方式はチャットルームに向いていません。

**HTTPリクエストは`client => server`の一方通行です**。サーバはクライアントの一つのリクエストに対して一つのレスポンスを返します。リクエストをもらわない限り、**サーバはクライアントにデータを送ることができません。**

チャットbotの場合、botからメッセージを送ることはないので良いものの、チャットルームの場合は必ずデータを送る側と受け取る側が存在します。

それを解決するために、[WebSoket](https://developer.mozilla.org/ja/docs/Web/API/WebSockets_API)を利用することができます。

WebSoketはクライアントとサーバの接続を確立して、どちらかが切るまでは双方向に通信することが出来ます。詳しい説明はしませんが、各ブラウザーとFastAPIはWebSoketをサポートしているので、簡単に利用することができます。

さて、今回の仕様はこのような感じです。

### 仕様
- pathは`/chat`
- クエリパラメータとしてnicknameをうけとる
- nicknameの指定がない場合は`unknown_{ipアドレス}`にする
- messageを受け取ったら、接続している全員にブロードキャストする
- 受け取る形はJSONで、以下のようになる
```json
{ "message": "contents" }
```
- ブロードキャストする形はJSONで、以下のようになる
```json
{ "nickname": "nickname", "message": "contents" }
```

### 作ってみよう

`backend/app/main.py`にこのように記述します

```python
from typing import List, Optional  # new

from fastapi import FastAPI, Body, WebSocket, WebSocketDisconnect  # new
from fastapi.middleware.cors import CORSMiddleware
import requests

from app import config  # さっきのAPI KEYをインポートしておく

app = FastAPI()

# CORSの設定を行っています
# 今回これはおまじないだと思ってください
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# new　ここから

# 接続したクライアントのリスト
active_ws_connections: List[WebSocket] = []


@app.websocket('/chat')
async def chat(websocket: WebSocket, nickname: Optional[str] = None):
    # 接続を受け取る
    await websocket.accept()
    # 接続中のclientを保持
    active_ws_connections.append(websocket)

    # クエリーの中のnicknameを取得
    # ない場合はunknown_{ipアドレス}にする
    if nickname is None:
        nickname = f'unknown_{websocket.client.host}'

    try:
        while True:
            # メッセージが送られるのを待つ
            # 形は{ "message": "contents" }
            data = await websocket.receive_json()
            # 受け取ったメッセージにnicknameを付与
            data['nickname'] = nickname
            # 全てのclientに送信
            # 形は{ "nickname": "nickname",　"message": "contents" }
            for connection in active_ws_connections:
                await connection.send_json(data)
    except WebSocketDisconnect:
        # 接続を切断された場合WebSocketDisconnectと言うエラーを吐くので
        # それを捕捉して接続リストから該当のもの削除する
        active_ws_connections.remove(websocket)


# new　ここまで


@app.post('/talk')
async def get_talk(query: str = Body(..., embed=True)):

    api_url = 'https://api.a3rt.recruit.co.jp/talk/v1/smalltalk'
    # form-data形式だと、このような記述になります
    form = {
        'apikey': (None, config.RECRUIT_API_KEY),  # このようにAPI KEYを使います
        'query': (None, query),
    }

    # postでリクエストを送ります
    res = requests.post(api_url, files=form)

    # レスポンスをJSONにdecodeして、そのまま返します
    res_json = res.json()

    return res_json


@app.get('/')
async def root():
    return {'message': 'Hello World'}


@app.get('/hello')
async def hello():
    return {'message': 'Hello there! I am Sei, welcome to myjlab!'}

```

クエリパラメータについて説明します。
```python
...
@app.websocket('/chat')
async def chat(websocket: WebSocket, nickname: Optional[str] = None):
    # 接続を受け取る
...
```

この部分の`nickname: Optional[str] = None`がクエリパラメータです。

このように記述すると、以下のようなURLを受け取ることができます。

`ws://localhost:8000/chat?nickname=sei`

ちなみに、この場合URLは4つのパートで構成されています。

- `ws://`
  - プロトコル。通信するプロトコルを指定します、ここでは`ws`、WebSoketです。
- `localhost:8000`
  - ドメイン。アクセスするサーバとポートを指定します。
- `/chat`
  - path(あるいはルート)。サーバのどのリソースにアクセスするかを指定します。
- `?nickname=sei`
  - query。クエリパラメータを指定します。

pathとqueryは複数指定することもできます。

e.g. `ws://localhost:8000/chat/path2/path3?nickname=sei&param1=value1&param2=value2`

pathも関数の引数として受け取ることができますが、ここでは詳しく説明しません。余力のある方は[FastAPIの公式チュートリアル](https://fastapi.tiangolo.com/ja/tutorial/path-params/)を参考にしてください。


## 確認
wsはSwaggerで確認することができませんので、確認はフロントを実装した後になります。

ここまでで、バックエンドの必須課題の部分は完了しました。お疲れ様です。

また、Stage3で会いましょう！