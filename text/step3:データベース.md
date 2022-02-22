# データベース

いよいよstep3になりました。step1と2はかなりbaby modeでお届けているつもりですが、いかがでしたか？

ここからはもう少しちゃんとしたアプリを作っていきたいと思います。フロントもvueでやってくれると思います。

LINEのUIをイメージに、こんな感じなwebアプリを作ってみようと思います。

![IMG_FB011593CBA7-1](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/IMG_FB011593CBA7-1.jpeg)

最初のこの章は設計とデータベースの実装ですが、、、発展課題なので、少し余談話から入りましょう。

# 余談：Pythonの型ヒント(typingモジュール)

step1と2のコードにこんか書く方が見られます。

```python
from typing import List, Optional
...

active_ws_connections: List[WebSocket] = []


@app.websocket('/chat')
async def chat(websocket: WebSocket, nickname: Optional[str] = None):
...

@app.post('/talk')
async def get_talk(query: str = Body(..., embed=True)):
...
```

変数はご存じと思うですが、変数の後ろについてる`: str`とかは、一体なんでしょう？

答えは変数の型です。この書き方がPythonの型ヒントです。（Python 3.5から）

上の表記はそれぞれ

| 変数                                     | 型                  |
| ---------------------------------------- | ------------------- |
| `query: str`                             | `str`               |
| `active_ws_connections: List[WebSocket]` | `WebSocket`の`list` |
| `websocket: WebSocket`                   | `WebSocket`         |
| `nickname: Optional[str]`                | `str`か`None`       |

前の変数は後ろの型を**期待している**という意味です。

でもただそうあって欲しいだけで、強制するものではありません。

**オリジナルのPython**では、型ヒントを**つけでもつけなくても、まったく同じ**です。

個別のライブラリとなると、そのヒントを基づいて処理をが変わる場合があります。

FastAPIがその一つです。FastAPIではその型から、リクエストのどの情報がどの変数に入れるべきかを推測します。

さらに、型を入れるのこんな嬉しいことがあります。

- エディタが型に応じてコードを自動補完くれます
- 読みすくなります
- ミスが減ります

型を入れることで、今書いてるコードがどういう目的なのかをさらに明確にすることができます。コードは書かれるよりも読まれることが多いとされていますので、ちゃんと型を入れた方が可読性の向上につながります。

最初は手間がもしれませんが、効率アップにつながるので、普段でもつけることを**強くお勧めします**。

型ヒントについて、｀FastAPIの作者はもっとたくさん[語ってくれています](https://fastapi.tiangolo.com/ja/python-types/)が、残念ながら公式の日本語翻訳はまだ[審査中](https://github.com/tiangolo/fastapi/pull/1899)ですので、[僕が翻訳したバージョン](http://kuroi.link/python-types.html)を載せます。詳しく知りたい方はぜひチェックしてください。

さて、余談はここまで、本題に入っていきましょう。

# 設計

LINE風なアプリを作るのですが、まずはどんな機能が必要なのかを考えてみましょう。

- 登録
- ログイン（認証）
- フレンド登録
- ユーザ情報の取得（フレンドリストを含む）
- メッセージ送信
- メッセージを履歴を取得

ざっとこんな感じです。となるとデータベースもシンプルに3テーブルに分けることができます。

| column   | aaa                                                       |
| -------- | --------------------------------------------------------- |
| id       | id<br> username<br> password                              |
| username | id<br> user_id<br> friend_id                              |
| password | id<br> datetime<br> sender_id<br> receiver_id<br> message |

# 実装

これから実装していきたいと思います。

## ファイル分け
ここからのコード全部`main.py`に書くとグチャグチャになりますので、ファイルを分けていきましょう。

まずは`backend/app`に`endpoint`のフォルダーを作ります。

さらに、`endpoint`
- `__init__.py`
- `routing.py`
- `chat_bot.py`
- `open_chat.py`

の四つのファイルを作ります。

今、`backend/app`の中のファイル構造はこうなりました。

```zsh
$ tree backend/app/
backend/app/
├── endpoint
│   ├── __init__.py
│   ├── chat_bot.py
│   ├── open_chat.py
│   └── routing.py
├── __init__.py
├── config.py
└── main.py
```
### `__init__.py`

`__init__.py`はPythonがこのファルダーがモジュールであることを認識されるために必要なものです。今はPythonのプロジェクトの場合ファイル分けときにフォルダーごとに一つ必要なファイルという認識で大丈夫だと思います。

今回ははこのファイルに何も書きません。

### `chat_bot.py`

チャットボットのエンドポイントをここに移しましょう。このように書きます。

```python
import requests
from fastapi import APIRouter, Body

from app import config

# appではなくて、ルーターを作成しています
router = APIRouter()


# pathはrootルーターで指定するのでここは空の文字例でいいです
@router.post('')  # <=== ここ注意
async def get_talk(query: str = Body(..., embed=True)):

    api_url = 'https://api.a3rt.recruit.co.jp/talk/v1/smalltalk'
    # form-data形式だと、このように記述になります
    form = {
        'apikey': (None, config.RECRUIT_API_KEY),  # こんなふうにAPI KEYを使います
        'query': (None, query),
    }

    # postでリクエストを送ります
    res = requests.post(api_url, files=form)

    # レスポンスをJSONにdecodeして、そもまま返します
    res_json = res.json()

    return res_json

```

### `open_chat.py`

オープンチャットのエンドポイントも同じです。ここに移しましょう。

```python
from typing import List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# 接続したクライアントのリスト
active_ws_connections: List[WebSocket] = []


# pathはrootルーターで指定するのでここは空の文字例でいいです
@router.websocket('')  # <=== ここも注意
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

```

### `routing.py`

それぞれのエンドポイントのルーターをroot_routerで管理します。

```python
from fastapi import APIRouter
# 各エンドポイントのルーターをimportします
from app.endpoint import chat_bot, open_chat

root_router = APIRouter()
# root_routerに読み込ませる
root_router.include_router(chat_bot.router, prefix='/chat_bot', tags=['chat_bot'])
root_router.include_router(open_chat.router, prefix='/open_chat', tags=['open_chat'])

```

`include_router`の`prefix`パラメーターでルーターのURLを指定します。

### `backend/app/main.py`

ファイルを分けると`main.py`はこのようになります。きれいになりましたね。

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.endpoint.routing import root_router

app = FastAPI()
# root_routerをappに読み込みます
app.include_router(root_router)  # new

# CORSの設定を行なっています
# 今回これはおまじないだと思ってください
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


# テスト用のエンドポイントは残しておきます
@app.get('/')
async def root():
    return {'message': 'Hello World'}


@app.get('/hello')
async def hello():
    return {'message': 'Hello there! I am Sei, welcome to myjlab!'}

```

### 確認

では`http://localhost:8080/docs#/`にアクセスしてみると。こちらもきれいに分けられましたね。

![20220222182523](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220222182523.png)

## DB：最初の一歩

まずはDBのフォルダも作っていきましょう。今回はSQLAlchemyというPythonのDB管理ライブラリを使います。

SQLAlchemyはオブジェクト風にDBを操作できるので、とても便利なライブラリです。

DBはMariaDBですが、今はMySQLの一種という認識で大丈夫です。

さて、DBに接続するにはユーザー名とパスワードが必要です。今回はあらかじめ環境に用意しました。

そういった機密性のある情報は`config.py`に書いておきましょう。

```python
RECRUIT_API_KEY = "DZ*********myapikey*********Mb"

MARIADB_USER = "mariadb"
MARIADB_PASSWORD = "secret"
MARIADB_HOST = "db"
MARIADB_DB_NAME = "myjchatapp"

```

次に、`backend/app`に`db`というフォルダーを作ります。

`db`フォルダーに

- `__init__.py`
- `base.py`

の2つのファイルを作ります。

`__init__.py`はあいかわらず何も書かなくでいいです。

`base.py`はDBに接続するためのファイルです。このように書きます。

```python
from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from app import config

# DB接続URLの構成は
# mysql+pymysql://ユーザー名:パスワード@ホスト名/データベース名
url = f'mysql+pymysql://{config.MARIADB_USER}:{config.MARIADB_PASSWORD}@{config.MARIADB_HOST}/{config.MARIADB_DB_NAME}'

# DBテーブルの基礎class
Base = declarative_base()
# DB接続用のエンジン
engine = create_engine(url, encoding='UTF-8', echo=True)

# 実際に接続するときに使うクラス
session = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ミドルウェア用関数
# あとで説明します
def get_db(request: Request):
    return request.state.db


```

