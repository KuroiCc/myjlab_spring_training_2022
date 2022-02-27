# データベース

いよいよStage3になりました。
Stage1と2はかなりbaby modeでお届けしてきたつもりですが、いかがでしたか？

ここからはもう少しちゃんとしたアプリを作っていきたいと思います。フロントもvueでやってくれると思います。

LINEのUIをイメージに、こんな感じのwebアプリを作ってみようと思います。

![IMG_FB011593CBA7-1](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/IMG_FB011593CBA7-1.jpeg)

最初のこの章は設計とデータベースの実装ですが、、、発展課題なので、少し余談話から入りましょう。

# 余談：Pythonの型ヒント(typingモジュール)

Stage1と2のコードにこのように書く方が見られます。

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

個別のライブラリとなると、そのヒントに基づいて処理をが変わる場合があります。

FastAPIがその一つです。FastAPIではその型から、リクエストのどの情報をどの変数に入れるべきかを推測します。

さらに、型を入れるとこんな嬉しいことがあります。

- エディタが型に応じてコードを自動補完してくれます
- 読みやすくなります
- ミスが減ります

型を入れることで、今書いているコードがどういう目的なのかをさらに明確にすることができます。コードは書かれるよりも読まれることが多いとされていますので、ちゃんと型を入れた方が可読性の向上につながります。

最初は手間かもしれませんが、効率アップにつながるので、普段からつけることを**強くお勧めします**。

型ヒントについて、｀FastAPIの作者はもっとたくさん[語ってくれています](https://fastapi.tiangolo.com/ja/python-types/)が、残念ながら公式の日本語翻訳はまだ[審査中](https://github.com/tiangolo/fastapi/pull/1899)ですので、[僕が翻訳したバージョン](http://kuroi.link/python-types.html)を載せます。詳しく知りたい方はぜひチェックしてください。

さて、余談はここまでにして、本題に入っていきましょう。

# 設計

LINE風なアプリを作るのですが、まずはどんな機能が必要なのかを考えてみましょう。

- 登録
- ログイン（認証）
- フレンド登録
- ユーザ情報の取得（フレンドリストを含む）
- メッセージ送信
- メッセージの履歴を取得

ざっとこんな感じです。となるとデータベースもシンプルに3テーブルに分けることができます。

| column   | aaa                                                       |
| -------- | --------------------------------------------------------- |
| id       | id<br> username<br> password                              |
| username | id<br> user_id<br> friend_id                              |
| password | id<br> datetime<br> sender_id<br> receiver_id<br> message |

# 実装

これから実装していきたいと思います。

## ファイル分け
ここからのコードを全部`main.py`に書くとグチャグチャになりますので、ファイルを分けていきましょう。

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

`__init__.py`はPythonがこのファルダーがモジュールであるということを認識するために必要なものです。今はPythonのプロジェクトの場合、ファイル分けのときにフォルダーごとに一つ必要なファイルという認識で大丈夫だと思います。

今回はこのファイルに何も書きません。

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

# CORSの設定を行っています
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

ここで`http://localhost:8080/docs#/`にアクセスしてみると・・・。こちらもきれいに分けられましたね。

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

`__init__.py`は変わらず何も書かなくでいいです。

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

これでDBに接続するための準備ができました。

## DB：modelの作成

次に、[設計](#設計)で決めたテーブルを実装していきましょう。

`backend/app/db/`に`models.py`というファイルを作って、このように書きます。

```python
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime

from app.db.base import Base
'''
Columnのパラメータの説明

primary_key: Trueは主キー
autoincrement: Trueは自動インクリメント
nullable: TrueはNULL許可する, Falseは不許可
unique: True重複禁止
'''


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(256), nullable=False, unique=True)
    password = Column(String(256), nullable=False)


class Friends(Base):
    __tablename__ = 'friends'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, primary_key=True)
    friend_id = Column(Integer, ForeignKey('users.id'), nullable=False, primary_key=True)


class Messages(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    datetime = Column(DateTime, nullable=False)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False, primary_key=True)
    receiver_id = Column(Integer, ForeignKey('users.id'), nullable=False, primary_key=True)
    message = Column(String(512), nullable=False)

```

モデルの実装ができたら、dbに接続して、テーブルを作成しましょう。ついでにデータも挿入してみましょう。

`backend/app/db/`に`init_db.py`というファイルを作って、このように書きます。

```python
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db.base import Base, engine, session
from app.db import models


# テーブル作成の関数
def create_tables(base, engine: Engine) -> None:
    base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    create_tables(Base, engine)

    # demoデータをDBに挿入する
    db_session: Session = session()
    user_in = models.Users(username='test_user', password='test_password')
    db_session.add(user_in)
    db_session.commit()
    # sessionのcloseは忘れずに
    db_session.close()
    '''
    以下のコマンドでdemoデータを挿入
    docker exec -it chat_app-backend-1 python3 /app/db/init_db.py

    以下のコマンドでDBの中身を確認できる
    docker exec -it chat_app-db-1 mysql --database=myjchatapp --user=mariadb --password=secret
    show tables;
    select * from users;
    '''

```

できたら、まずはdockerの環境を確認してみよう！

`docker ps`、このコマンドで実行中のコンテナを確認します。  

![20220223175313](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220223175313.png)

手順通り行えば、最後の`NAMES`の列に`chat_app-backend-1`と`chap_app-db-1`という二つのコンテナがあるはずです。

`chat_app-backend-1`がバックエンドのコンテナ

`chap_app-db-1`がデータベースのコンテナ

違う場合は、それぞれの`NAMES`を覚えておきましょう。

確認できたら、以下のコマンドでバックエンドコンテナの内部に`init_db.py`を実行しましょう。

コンテナ名が違う場合は`chat_app-backend-1`のところを対応するものに変えてください。

```bash
docker exec -it chat_app-backend-1 python3 /app/db/init_db.py
```

実行してみると、

![20220223181747](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220223181747.png)

このような出力が出ると思います。

これでDBにテーブルを作成したので、それを確認してみましょう。

以下のコマンドでデータベースコンテナの内部に入ります。

```bash
docker exec -it chat_app-db-1 mysql --database=myjchatapp --user=mariadb --password=secret
```

次に`show tables;`と入力して実行してみると、

![20220223182848](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220223182848.png)

テーブルが、できています！

ではデータの方は？`select * from users;`このコマンドで確認しましょう！

![20220223183136](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220223183136.png)

これもできています！素晴らしい！

## パスワードの暗号化


前の章で無事にデータを挿入したものの、このままでは一つ問題がございます。Stage1ではパスワードとかは平文で書くべきではないと言いました。これはDBの内部においても同じです。

だから、パスワードを暗号化してDBに入れましょう。

今回はFastAPI公式推奨のPassLibというライブラリでパスワードのハッシュ処理をします。

`backend/app/`に`security.py`というファイルを作って、このように書きます。

```python
from passlib.context import CryptContext

# ハッシュ化のアルゴリズムを指定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

```

次に`backend/app/db/models.py`の`Users`クラスを書き足します。

```python
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime

from app.db.base import Base
from app.security import get_password_hash  # new

...

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(256), nullable=False, unique=True)
    password = Column(String(256), nullable=False)

    # passwordをハッシュ化して保存する
    def __init__(self, *, id: int = None, username: str, password: str) -> None:  # new
        super().__init__(id=id, username=username, password=get_password_hash(password))  # new

...
```

これで、データを入れる時自動でハッシュ化されます。


## CRUDモジュール

さて、新しくデータを入れてみたいですが、その前にCRUDモジュールを作りましょう。

CRUDとは、Create, Read, Update, Deleteの略です。

DBの対する操作はこの4つにまとめることができます。

では、CRUDモジュールって・・・？

前の章で行っているuserの挿入は、DBを **"直接"** 操作しています。

なので、**"危険な"** 操作をしても、DBはそのまま受け付けてしまう場合があります。

"危険な"操作の定義は仕様によりますが、例えば、

- 自分のidを友人として登録する
- 銀行などで振込の場合、振込元-100、振込先+200

などなど...

DBも挿入データに制限をかけたりすることができますが、カバーしきれない場合もあります。

ですので、DBに"直接"操作するのではなくて、必要な操作をとあるモジュールにまとめて、そのモジュールを通じてのみDBを操作すればミスの削減につながります。（ここはCRUDモジュールと呼んでいますが、現場によっては全く違う呼び方する可能性もあるので、そこだけ気をつけましょう。）

ほかにもコードの記述量が減ったりとか、メリットはたくさんあるので、CRUDモジュールを作りましょう。

`backend/app/db/`に`crud.py`というファイルを作って、このように書きます。

```python
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import Users


class CRUDUser():
    # コンストラクタでに自身のテーブルmodelを指定
    def __init__(self, model: Users) -> None:
        self.model = model

    def create(self, db_session: Session, *, obj_in: Users) -> Users:
        db_session.add(obj_in)
        db_session.commit()
        db_session.refresh(obj_in)
        return obj_in

    def get(self, db_session: Session, id: int) -> Optional[Users]:
        return db_session.query(self.model).filter(self.model.id == id).first()


# 実際に使用するインスタンス
user = CRUDUser(Users)

```

できたらデータを挿入してみましょう。実はdemoデータも少し用意しましたので、それを挿入しましょう。

`backend/app/db/`に`demo_data.json`というファイルを作って、デモデータの内容をコピペしてください。

量が多いので、読みやすくするために、デモデータはこの[ページの最後](#デモデータ)に置いています。

次は、`backend/app/db/init_db.py`にを変更しましょう。

```python
import json  # new
from typing import List  # new

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db.base import Base, engine, session
from app.db import models
from app.db import crud  # new


def create_tables(base, engine: Engine) -> None:
    base.metadata.create_all(bind=engine)


# new
# デモデータを挿入するための関数
def insert_demo_users(session: Session, users: List) -> None:
    for user in users:
        user_in = models.Users(**user)
        crud.user.create(session, obj_in=user_in)


if __name__ == "__main__":
    create_tables(Base, engine)

    # new
    # demoデータを読み込む
    with open("/app/db/demo_data.json", "r") as fp:
        demo_data = json.load(fp)

    # demoデータをDBに挿入する
    # withを使えば、自動的にcloseしてくれる
    with session() as db_session:  # new
        insert_demo_users(db_session, demo_data['users'])  # newÏ
    '''
    以下のコマンドでdemoデータを挿入
    docker exec -it chat_app-backend-1 python3 /app/db/init_db.py

    以下のコマンドでDBの中身を確認できる
    docker exec -it chat_app-db-1 mysql --database=myjchatapp --user=mariadb --password=secret
    show tables;
    select * from users;
    '''

```

`insert_demo_users`引数の書き方`**user`は`dict`をアンパックしています。詳しくは[この記事](https://tksmml.hatenablog.com/entry/2019/05/02/000000)を参照してください。

`tuple`のアンパックはプロ基礎で習っていると思います。

ではもう一度このコマンドを実行します。
```bash
docker exec -it chat_app-backend-1 python3 /app/db/init_db.py
```

そしたら以下のコマンドでDBの中身を確認できます。

```bash
docker exec -it chat_app-db-1 mysql --database=myjchatapp --user=mariadb --password=secret
select * from users;
```

![20220223234837](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220223234837.png)

っで、できた！ちゃんとパスワードも暗号化されています！

ここまでできたあなた、そうそこのあなた！天才かもしれません！

ここでデータベースの作成は完了です！おつかれさまでした！


# デモデータ

[ここから](#CRUDモジュール)戻れます。

```json
{
    "users": [
        {
            "id": 101,
            "username": "{ここ自分の名前に変えてね}",
            "password": "{好きなパスワードを入れてね}"
        },
        {
            "id": 102,
            "username": "sei",
            "password": "sei1000"
        },
        {
            "id": 103,
            "username": "ren",
            "password": "ren1000"
        },
        {
            "id": 104,
            "username": "ami",
            "password": "ami1000"
        },
        {
            "id": 105,
            "username": "yuzuka",
            "password": "yuzuka1000"
        },
        {
            "id": 106,
            "username": "ozeki",
            "password": "ozeki1000"
        },
        {
            "id": 107,
            "username": "MIYAJI",
            "password": "MIYAJI1000"
        }
    ],
    "friends": [
        {
            "user_id": 101,
            "friend_id": 102
        },
        {
            "user_id": 101,
            "friend_id": 103
        },
        {
            "user_id": 102,
            "friend_id": 103
        },
        {
            "user_id": 103,
            "friend_id": 104
        },
        {
            "user_id": 102,
            "friend_id": 104
        },
        {
            "user_id": 101,
            "friend_id": 105
        },
        {
            "user_id": 102,
            "friend_id": 106
        },
        {
            "user_id": 104,
            "friend_id": 107
        }
    ],
    "messages": [
        {
            "datetime": "2021-03-23T20:40:26",
            "sender_id": 101,
            "receiver_id": 102,
            "message": "こんにちは"
        },
        {
            "datetime": "2021-11-13T04:19:47",
            "sender_id": 101,
            "receiver_id": 103,
            "message": "おやすみなさい"
        },
        {
            "datetime": "2021-11-24T12:17:12",
            "sender_id": 102,
            "receiver_id": 103,
            "message": "遊ぼうよ"
        },
        {
            "datetime": "2021-07-02T01:32:48",
            "sender_id": 103,
            "receiver_id": 104,
            "message": "お腹すいた"
        },
        {
            "datetime": "2021-07-05T10:52:33",
            "sender_id": 102,
            "receiver_id": 104,
            "message": "ありがとう"
        },
        {
            "datetime": "2021-09-08T10:18:41",
            "sender_id": 101,
            "receiver_id": 105,
            "message": "今日はいい天気だね"
        },
        {
            "datetime": "2021-03-02T01:52:52",
            "sender_id": 102,
            "receiver_id": 106,
            "message": "ごめんなさい"
        }
    ],
    "groups": [
        {
            "id": 101,
            "name": "myjlab-1"
        },
        {
            "id": 102,
            "name": "myjlab-2"
        },
        {
            "id": 103,
            "name": "myjlab-3"
        },
        {
            "id": 104,
            "name": "myjlab-4"
        },
        {
            "id": 105,
            "name": "rabbit"
        },
        {
            "id": 106,
            "name": "gorilla"
        },
        {
            "id": 107,
            "name": "tomato"
        }
    ],
    "groups_members": [
        {
            "group_id": 101,
            "user_id": 101
        },
        {
            "group_id": 101,
            "user_id": 102
        },
        {
            "group_id": 101,
            "user_id": 103
        },
        {
            "group_id": 101,
            "user_id": 104
        },
        {
            "group_id": 102,
            "user_id": 105
        },
        {
            "group_id": 102,
            "user_id": 106
        },
        {
            "group_id": 103,
            "user_id": 107
        },
        {
            "group_id": 104,
            "user_id": 101
        },
        {
            "group_id": 105,
            "user_id": 102
        },
        {
            "group_id": 106,
            "user_id": 103
        },
        {
            "group_id": 107,
            "user_id": 104
        },
        {
            "group_id": 103,
            "user_id": 105
        },
        {
            "group_id": 104,
            "user_id": 102
        },
        {
            "group_id": 105,
            "user_id": 104
        },
        {
            "group_id": 106,
            "user_id": 104
        },
        {
            "group_id": 107,
            "user_id": 102
        }
    ],
    "groups_messages": [
        {
            "datetime": "2021-03-23T20:40:26",
            "group_id": 101,
            "sender_id": 101,
            "message": "ありがとう"
        },
        {
            "datetime": "2021-11-13T04:19:47",
            "group_id": 101,
            "sender_id": 102,
            "message": "おはよう"
        },
        {
            "datetime": "2021-11-24T12:17:12",
            "group_id": 102,
            "sender_id": 105,
            "message": "ありがとう"
        },
        {
            "datetime": "2021-07-02T01:32:48",
            "group_id": 103,
            "sender_id": 105,
            "message": "こんにちは"
        },
        {
            "datetime": "2021-07-05T10:52:33",
            "group_id": 104,
            "sender_id": 102,
            "message": "猫が好きです"
        },
        {
            "datetime": "2021-09-08T10:18:41",
            "group_id": 105,
            "sender_id": 104,
            "message": "猫は可愛いですね"
        },
        {
            "datetime": "2021-03-02T01:52:52",
            "group_id": 106,
            "sender_id": 104,
            "message": "今日は寒いですね"
        },
        {
            "datetime": "2021-10-10T09:21:33",
            "group_id": 107,
            "sender_id": 102,
            "message": "野球は面白いですね"
        }
    ]
}
```