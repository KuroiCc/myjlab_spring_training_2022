# 個人チャット

DBもセキュリティーも整備できたので、次はどんどんエンドポイントを実装して行けばアプリが完成されます。

あくまでも個人的な（実務経験がない人の）やり方ですが、私は基本的に以下のような流れでエンドポイントを開発します。

1. 機能と仕様の設計
2. リクエストとリスポンスのモデルの実装
3. crud操作の実装
4. エンドポイントの実装

ちなみに実際では、フロントエンドとバックエンドが同時に開発していることが多いので、最初にインターフェースを決めることが一番大事です。どんなエンドポイントを提供するか、各エンドポイントはどんな形のデータでやり取りするか、それを決めないと、何もはじまりません。

今回は個人チャットのパートでは、以下6つのエンドポイントをこの順番で実装していきます。

- ユーザ登録
- フレンド情報取得
- フレンド追加
- ログイン（ユーザ情報取得）(修正)
- ws接続エンドポイント
- チャットの送信
- チャット履歴の取得

実際の仕様はこの章の[最後](#仕様)にまとめて記載しますので、挑戦したい人はそこから作ってみてください。

なお、今回はそんなに凝ったアプリではないので、エラー処理はお気持程度で止まりたいと思います。

## ユーザ登録

最初は一番簡単なユーザ登録から実装していきます。

機能はズバリユーザ登録です。crudはcreateをそもまま使います。

レスポンススキーマは`User`と同じなので、リクエストスキーマだけ作ればおわりです。

`app/endpoints/schemas.py`に書き込みます。

```python
class UserCreate(BaseModel):
    username: str
    password: str

```

次は`app/endpoints/`に`user.py`を作って書き込みます。

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import crud
from app.db.base import get_db
from app.db.models import Users as DBUser
from app.endpoint.schemas import User, UserCreate

router = APIRouter()


@router.post('/register', response_model=User)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    db_user = DBUser(**user_in.dict())
    return crud.user.create(db, obj_in=db_user)

```

FastAPIでbodyのパラメータを指定する場合、関数に引数の型を`pydantic.BaseModel`のクラスを指定するだけでできます。

今回順番がちょっと違ったが実はこういう書き方が一番よく使います。

次はroot_routerに読み込ませましょう。

`app/endpoints/routing.py`に書き込みます。

```python
from fastapi import APIRouter
# 各エンドポイントのルーターをimportします
from app.endpoint import chat_bot, open_chat, login, user  # new

root_router = APIRouter()
# root_routerに読み込ませる
root_router.include_router(chat_bot.router, prefix='/chat_bot', tags=['chat_bot'])
root_router.include_router(open_chat.router, prefix='/open_chat', tags=['open_chat'])
root_router.include_router(login.router, prefix='/login', tags=['login'])
root_router.include_router(user.router, prefix='/user', tags=['user'])  # new

```

こでれ完了！確認していきましょう。

`http://localhost:8080/docs`にアクセス！

`/user/register`が表示されるはずと思うので、"Try it out"をクリックして、usernameとpasswordを変更してexecuteすると

![20220228141338](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220228141338.png)

![20220228141412](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220228141412.png)


idもちゃんと返されていますね、素晴らしい！

## フレンド情報取得

機能はログインしているユーザのフレンド情報を取得する

GETなので、リクエストスキーマはなし、レスポンススキーマは`User`のリストなので、追加もなしです。

なので、crudを作っていきたいと思います。このcrud操作はおそらくこのアプリにおいて一番難しいの思いますので、まずは実装の設計を少し考えましょう。

`friends`テーブルの設計は以下の通りです。（再掲）

| friends   |
| --------- |
| id        |
| user_id   |
| friend_id |

これはチャットアプリなので、一度でもフランド登録すれば、お互いフレンドになります。

つまり、例えばDBに以下のレコードがあった場合、

| id  | user_id | friend_id |
| --- | ------- | --------- |
| 0   | 101     | 102       |


`id: 101`のユーザのフレンド情報を取得するとき、`id: 102`は含まれるはずです。

その逆場合、`id: 102`のユーザのフレンド情報に、`id: 101`も含まれるはずです。

なので、自分のすべてのフレンドの`id`を取り出したい場合は

- 自分の`id`が`user_id`であるときの全てのレコードの`friend_id`
- 自分の`id`が`friend_id`であるときの全てのレコードの`user_id`

を取り出して、さらに重複するものを取り除く必要があります。

具体的な実装は以下のようになります。

`app/db/crud.py`に書き込みます。

```python
from typing import Optional, List  # new

from sqlalchemy.orm import Session

from app.db.models import Users, Friends  # new


class CRUDUser():
    # コンストラクタでに自信のテーブルmodelを指定
    def __init__(self, model: Users, friend_model: Friends) -> None:  # new
        self.model = model
        self.friend_model = friend_model  # new

    ...

    ...

    # new ここから
    def get_friends(self, db_session: Session, user_id: int) -> List[Users]:
        # idがuser_idである場合のfriend_id
        query1 = db_session\
            .query(self.friend_model.friend_id)\
            .filter(self.friend_model.user_id == user_id)
        # idがfriend_idである場合のuser_id
        query2 = db_session\
            .query(self.friend_model.user_id)\
            .filter(self.friend_model.friend_id == user_id)

        # 合併して、重複を取り除く
        friend_id_list = query1.union(query2).all()

        # idを元ついてユーザ情報を取得して返す
        # この書き方はpythonの内包表記
        return [self.get(db_session, friend_id[0]) for friend_id in friend_id_list]


# 実際に使用するインスタンス
user = CRUDUser(Users, Friends)  # new

```

returnの方は内包表記という便利な書き方です、こでは詳しく説明しませんので、詳しくはGoogle先生まで。

では、エンドポイントを作っていこう！

`app/endpoints/user.py`に書き込みます。

```python
from typing import List  # new

from fastapi import APIRouter, Depends

...

...

from app.endpoint.schemas import User, UserCreate
from app.security import auth  # new

...

...


# new ここから
@router.get('/get_friends', response_model=List[User])
def get_friends(
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(auth),
):

    return crud.user.get_friends(db, current_user.id)

```

`http://localhost:8080/docs`で確認してもいいですが、データが入ってないので空のリストが返ってくる思うので、フレンド登録ができた後一度に確認していきたいと思います。


### フレンド追加

機能はログインしているユーザのフレンドリストに新しいユーザの追加です。

レスポンススキーマはフレンド登録と同じで、リクエストスキーマは`friend_id`だけなので、追加コードなしです。

crudを実装していきたいと思います。

一つだけ説明しますが、以下の二つのレコード

| id  | user_id | friend_id |
| --- | ------- | --------- |
| 1   | 101     | 102       |
| 2   | 102     | 101       |

はこのアプリにおいて、同じ意味を持ちますので、それの挿入も避けたいと思います。

`app/db/crud.py`に書き込みます。

```python
class CRUDUser():
 
    ...

    def add_friend(self, db_session: Session, user_id: int, friend_id: int):
        # 自分を友達に追加しようとした場合はエラーを吐く
        if user_id == friend_id:
            raise ValueError("user_id and friend_id is same")

        if user_id > friend_id:
            # 重複追加を防ぐ
            # ex) user_id = 1, friend_id = 2
            #    user_id = 2, friend_id = 1
            user_id, friend_id = friend_id, user_id
        friend_in = self.friend_model(user_id=user_id, friend_id=friend_id)
        db_session.merge(friend_in)
        db_session.commit()

        return self.get_friends(db_session, user_id)

...
```

次はエンドポイントを作っていきます。

`app/endpoints/user.py`に書き込みます。

```python
from typing import List

from fastapi import APIRouter, Depends, Body, HTTPException  # new
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError  # new

...

...

@router.post('/add_friend', response_model=List[User])
def add_friend(
    friend_id: int = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(auth),
):
    try:
        friends = crud.user.add_friend(db, current_user.id, friend_id)
    except ValueError as e:
        # 自分で定義した自分を友達に追加しようとした場合にはくエラー
        raise HTTPException(status_code=400, detail=f'{e}')
    except IntegrityError:
        # 存在したいuserを挿入しようとした場合、このエラー吐く
        raise HTTPException(status_code=404, detail='User or Friend not found')

    return friends

```

`IntegrityError`は存在していユーザを挿入しようとした場合、SQLAlchemyがはいてくれるエラーです。

フレンドのデモデータも用意していますので、それをDBに挿入していきたいと思います。

`app/db/init_db.py`に書き込みます。

```python
...

# デモデータを挿入するための関数
def insert_demo_users(session: Session, users: List) -> None:
    for user in users:
        user_in = models.Users(**user)
        crud.user.create(session, obj_in=user_in)


# new
def insert_demo_friends(session: Session, friends: List) -> None:
    for friend in friends:
        crud.user.add_friend(session, user_id=friend["user_id"], friend_id=friend["friend_id"])

...

...

    # demoデータをDBに挿入する
    # withを使えば、自動的にcloseしてくれる
    # ! 挿入済みのデータはコメントアウトしましょう
    with session() as db_session:  # new
        # insert_demo_users(db_session, demo_data['users'])  # これはコメントアウト
        insert_demo_friends(db_session, demo_data['friends'])  # new
...

```

userは前に挿入済みなので、重複挿入はエラーが起きますので、コメントアウトします。

では前にも使ったこのコマンドでデータを挿入してみましょう。

`docker exec -it chat_app-backend-1 python3 /app/db/init_db.py`


さて、フレンド取得も含めて確認していきましょう。

`http://localhost:8080/docs`にアクセスします。

authorizeで登録して、get_friendsのエンドポイントを実行してみると

![20220228202742](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220228202742.png)

ちゃんとフレンドが取得できていることがわかります。

次はadd_friendのエンドポイントでフレンドではない104のユーザを追加してみと

![20220228202902](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220228202902.png)

![20220228202927](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220228202927.png)

104のユーザは入ったフレンドリストが返されていますね。素晴らしい！！

### ログイン（ユーザ情報取得）の修正

ログインするとき、基本のユーザー情報だけでなく、フレンドリストも一緒に返したいので、ログインのエンドポイントを修正していきたいと思います。

まずは新しいレスポンススキーマを作ります。

`app/endpoints/schemas.py`に書き込みます。

```python
from typing import List  # new

...

...


# new
class LoginUser(BaseModel):
    id: int
    username: str
    friends: List[User]

    class Config:
        orm_mode = True

```

crudは前に書いたのでパスします。

次はエンドポイントを修正します。

`app/endpoints/login.py`を修正します。

```python
...
from app.db.models import Users as DBUser
from app.endpoint.schemas import LoginUser  # new
from app.security import auth

router = APIRouter()


@router.get('', response_model=LoginUser)  # new
def login(
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(auth),
):

    current_user.friends = crud.user.get_friends(db, current_user.id)  # new
    return current_user

```

`http://localhost:8080/docs`にauthorizeで登録して、loginのエンドポイントを確認してみると

![20220228204200](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220228204200.png)

できています。素晴らしい！！

## ws接続エンドポイント

ここからはmessageに関するエンドポイントです。

wsでメッセージをクライアントに送るので、最初はws接続を確立する必要があります。

wsの接続エンドポイントなのでスキーマはなし、crudもなしです。

`path`は`/login/ws_connect`なので、

`app/endpoints/login.py`を編集していきましょう。

```python
from typing import List, Dict  # new

from fastapi import APIRouter, Depends, WebSocket, HTTPException, WebSocketDisconnect  # new
from sqlalchemy.orm import Session
import json  # new

from app.db import crud
from app.db.base import get_db, session  # new
from app.db.models import Users as DBUser
from app.endpoint.schemas import LoginUser
from app.security import auth, security  # new

router = APIRouter()


@router.get('', response_model=LoginUser)
def login(
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(auth),
):

    current_user.friends = crud.user.get_friends(db, current_user.id)
    return current_user


# new ここから
class ConnectionManager:
    """
    websocket connectionを管理するクラス
    {user_id: websocket}のような辞書型でconnection管理する
    """
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        # 多重ログインを防ぐ
        if user_id in self.active_connections:
            raise HTTPException(status_code=4001, detail='Already connected')
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        self.active_connections.pop(user_id)

    async def send_personal_message(self, message: str, user_id: int):
        await self.active_connections[user_id].send_text(message)

    async def broadcast(self, message: str, scope: List[int] = None):
        """
        ブロードキャストする

        *param scope: 対象のuser_idのリスト, 指定がない場合は全員
        """
        if scope is None:
            scope = self.active_connections.keys()

        for connection in scope:
            await self.active_connections[connection].send_text(message)


ws_manager = ConnectionManager()


@router.websocket('/ws_connect')
async def ws_connect(websocket: WebSocket, basic: str):
    # wsフロントからではheaderを送れないので
    # クエリパラメータでkeyを受け取って、バックでheaderに入れる
    key, value = 'Authorization', f'Basic {basic}'
    websocket.headers._list.append((key.lower().encode("latin-1"), value.encode("latin-1")))
    # depends使わずにマニアルでcurrent_userを取得
    with session() as db:
        current_user = auth(db=db, credentials=await security(websocket))
    # !ここらへんの認証関連は分からなくでいいです

    # 接続されたら、ws_managerに登録
    await ws_manager.connect(websocket, current_user.id)
    try:
        while True:
            # 送信専用なので、受信したらエラーメッセージを送る
            await websocket.receive_text()
            mes = json.dumps({"err": "you should't send any message using ws"})
            await ws_manager.send_personal_message(mes, current_user.id)
    except WebSocketDisconnect:
        # 接続が切れたら、ws_managerから削除
        ws_manager.disconnect(current_user.id)

```

大部足しましたね。大勢のwsの接続管理するときは、こうやってクラスを作った方がラクで間違いにくいです。

wsの認証関連のとことは、フロントではwsのheaderを変更するのは難しいみたいので、クエリでkeyを受け取って、無理やりheaderに入れて今使ってる`auth`関数に対応させています。ここは難しいので、分からないなら素直にコピペしてもいいと思います。

これでws接続エンドポイントは完成です。確認は残念ながらフロントができるまでできません。

## チャットの送信

個人チャット終わるまでエンドポイントは残り二つです。

もう少しがんばりましょう！

このエンドポイントの機能は
- メッセージをDBに保存
- 自分と相手（ログインしている場合）wsそのメッセージを送信

なので、まずはスキーマを実装していきましょう！

`app/endpoints/schemas.py`に

```python
from typing import List
from datetime import datetime  # new

...
...

class UserCreate(BaseModel):
    username: str
    password: str


# new ここから
class ReceivePersonalMessage(BaseModel):
    datetime: datetime
    receiver_id: int
    message: str


class SendPersonalMessage(ReceivePersonalMessage):
    id: int
    sender_id: int

    class Config:
        orm_mode = True
# new ここまで


class LoginUser(BaseModel):
...
```

次はmessagesのcrudです。CRUDUserの`__init__`と`create`とほぼ同じです。

ここはbaseのCRUDクラスを作って継承していくの方がよいですが、ややこしいので今回はやめます。

`app/db/crud.py`に

```python
from typing import Optional, List

from sqlalchemy.orm import Session

from app.db.models import Users, Friends, Messages  # new


class CRUDUser():
...

...


# new ここから
class CRUDMessage():

    def __init__(self, model: Messages) -> None:
        self.model = model

    def create(self, db_session: Session, *, obj_in: Messages) -> Messages:
        db_session.add(obj_in)
        db_session.commit()
        db_session.refresh(obj_in)
        return obj_in


# 実際に使用するインスタンス
user = CRUDUser(Users, Friends)
message = CRUDMessage(Messages)  # new

```

次はエンドポイントです。

`app/endpoints/`に`messages.py`を作成して、このように書きます。

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import json

from app.endpoint.login import ws_manager
from app.db import crud
from app.db.base import get_db
from app.db.models import Users as DBUser, Messages as DBMessage
from app.security import auth
from app.endpoint.schemas import ReceivePersonalMessage, SendPersonalMessage

router = APIRouter()


@router.post('/send_personal_chat')
async def send_personal_message(
    received_msg: ReceivePersonalMessage,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(auth),
):
    # received_msgからDBのMessagesを作成
    msg_in = DBMessage(**received_msg.dict(), sender_id=current_user.id)
    try:
        # 挿入
        db_msg = crud.message.create(db, obj_in=msg_in)
    except IntegrityError:
        # 存在しないユーザーにメッセージを送るとき、このエラー吐く
        raise HTTPException(status_code=404, detail='user not found')

    # 送る用にデータの形を変える
    send_msg = {"personal_message": SendPersonalMessage.from_orm(db_msg)}
    send_msg = json.dumps(jsonable_encoder(send_msg))

    # ログインしている場合セッメージ送る
    for user_id in (db_msg.sender_id, db_msg.receiver_id):
        if user_id in ws_manager.active_connections.keys():
            await ws_manager.send_personal_message(send_msg, user_id)

    return 'Succeed'

```

データを送信用に形を変更しているときに使った`from_orm`メソッドと`jsonable_encoder`について説明します。

pydanticの`BaseModel`は便利なメソッドを用意しています。`from_orm`メソッドがその一つです。`from_orm`メソッドはsqlalchemyのモデルからpydanticのモデルに変換することができる。FastAPIの内部にもその方式でsqlalchemyのモデルを処理しています。

`jsonable_encoder`についてですは

jsonには`datetime`という型がないので、そいった型はそのままではjsonに変換できません。FastAPIでは`jsonable_encoder`という関数を用意しているので、それを使うと大抵のデータ型は`json.dumps`（jsonの文字列に変換する関数）ができるオブジェクトに変換されます。

これでメッセージ送信のエンドポイントが実装できました。

確認はチャット履歴取得エンドポイントを合わせてやりたいと思います。

## チャット履歴の取得

いよいよ個人チャット最後のエンドポイントです。

機能はログインしているユーザと相手のチャット履歴の取得です。

メソットはGETで、クエリパラメータは以下の四つ
- receiver_id: int
  - 相手のユーザID
- skip: int
  - 取得するチャット履歴の最初の位置
- limit: int
  - 取得するチャット履歴の最大件数
- desc: bool
  - true: 降順
  - false: 昇順

履歴の取得は、例えば3年間一万以上の履歴をログインするたびに取得するのはどちらにとっても大変なので、取得する範囲を限定できるようにする必要があります。

`skip`、`limit`はどこから最大何件取得するかを指定します。

`desc`は、取得したものは時間の降順か昇順かを指定します。

スキーマは`SendPersonalMessage`を使います。

ではcrudを実装していきましょう。

`app/db/crud.py`に

```python
...

class CRUDMessage():

    ...

    def get_chat_messages(
        self,
        db_session: Session,
        sender_id: int,
        receiver_id: int,
        *,
        skip: int = 0,
        limit: int = 20,
        desc: bool = True,
    ) -> List[Messages]:
        '''
        skip: 何件目から取得するか
        limit: 取得する最大件数
        desc: 降順か昇順
        '''
        # 自分が送ったメッセージ
        sended_msg = db_session\
            .query(self.model)\
            .filter(self.model.sender_id == sender_id)\
            .filter(self.model.receiver_id == receiver_id)
        # 自分が受け取ったメッセージ
        received_msg = db_session\
            .query(self.model)\
            .filter(self.model.sender_id == receiver_id)\
            .filter(self.model.receiver_id == sender_id)

        # 時間の降順か昇順を指定
        order_by = self.model.datetime.asc() if desc else self.model.datetime.desc()
        return sended_msg.union(received_msg).order_by(order_by).offset(skip).limit(limit).all()


# 実際に使用するインスタンス
user = CRUDUser(Users, Friends)
message = CRUDMessage(Messages)

```

次はエンドポイント、

`app/endpoints/messages.py`に

```python
from typing import List  # new

...

...


@router.get('/personal_chat_history', response_model=List[SendPersonalMessage])
def get_personal_chat_history(
    receiver_id: int,
    skip: int = 0,
    limit: int = 20,
    desc: bool = True,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(auth),
):

    try:
        messages = crud.message.get_chat_messages(
            db,
            sender_id=current_user.id,
            receiver_id=receiver_id,
            skip=skip,
            limit=limit,
            desc=desc,
        )
    except IntegrityError:
        # 存在しないユーザーにメッセージを送るとき、このエラー吐く
        raise HTTPException(status_code=404, detail='user not found')

    return messages

```

`messages.py`は新しく作ったので、root_routerに追加しましょう。

`app/endpoints/routing.py`に

```python
from fastapi import APIRouter
# 各エンドポイントのルーターをimportします
from app.endpoint import chat_bot, open_chat, login, user, message  # new

root_router = APIRouter()
# root_routerに読み込ませる
root_router.include_router(chat_bot.router, prefix='/chat_bot', tags=['chat_bot'])
root_router.include_router(open_chat.router, prefix='/open_chat', tags=['open_chat'])
root_router.include_router(login.router, prefix='/login', tags=['login'])
root_router.include_router(user.router, prefix='/user', tags=['user'])
root_router.include_router(message.router, prefix='/message', tags=['message'])  # new

```

messageのデモデータも用意しているので、挿入していきましょう。

`app/db/init_db.py`に

```python
...

def insert_demo_friends(session: Session, friends: List) -> None:
    for friend in friends:
        crud.user.add_friend(session, user_id=friend["user_id"], friend_id=friend["friend_id"])


# new
def insert_demo_messages(session: Session, messages: List) -> None:
    for message in messages:
        crud.message.create(session, obj_in=models.Messages(**message))


if __name__ == "__main__":
    create_tables(Base, engine)

    # demoデータを読み込む
    with open("/app/db/demo_data.json", "r") as fp:
        demo_data = json.load(fp)

    # demoデータをDBに挿入する
    # withを使えば、自動的にcloseしてくれる
    # ! 挿入済みのデータはコメントアウトしましょう
    with session() as db_session:  # new
        # insert_demo_users(db_session, demo_data['users'])
        # insert_demo_friends(db_session, demo_data['friends'])
        insert_demo_messages(db_session, demo_data['messages'])  # new
...
```

friendsは挿入済みなので、コメントアウトは忘れずに

おなじみのこのコマンドで、データを挿入していきましょう。

`docker exec -it chat_app-backend-1 python3 /app/db/init_db.py`

wsの部分は確認できないのは残念ですが、できるところまで確認していきましょう。

`http://localhost:8080/docs`にauthorizeで登録して、

まずは`messages/send_personal_message`

![20220302012038](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220302012038.png)

![20220302012054](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220302012054.png)

Succeed、美しい単語！

では`messages/get_personal_chat_history`の方は？

![20220302012345](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220302012345.png)

![20220302013043](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220302013043.png)

demo dataの挿入よし

さっき入れたメッセージよし

並び順よし

個人チャット〜〜〜〜〜〜完了！！！

次はグループチャット編、今度こそ最後です。

## 仕様

### ユーザ登録
- path: `/user/register`
- method: POST
- 機能：新しいユーザをDBに登録する
- リクエストスキーマ:application/json
```json
{
  "username": "string",
  "password": "string"
}
```
- レスポンススキーマ: application/json
```json
{
  "id": 0,
  "username": "string"
}
```

### フレンド情報取得
- path: `/user/get_friends`
- method: GET
- 機能：ログインしているユーザのフレンド情報を取得する
- レスポンススキーマ: application/json
```json
[
  {
    "id": 0,
    "username": "string"
  },
  {
    "id": 0,
    "username": "string"
  }
]
```

### フレンド追加
- path: `/user/add_friend`
- method: POST
- 機能: ログインしているユーザのフレンドリストに新しいユーザを追加する
- リクエストスキーマ:application/json
```json
{
  "friend_id": 0
}
```
- レスポンススキーマ: application/json
  - 新しいフレンドリストを返す
  - フレンド情報取得と同じ

### ログイン（ユーザ情報取得）
- path: `/login`
- method: GET
- 機能：ログインしているユーザのユーザ情報を取得する
- レスポンススキーマ: application/json
```json
{
  "id": 0,
  "username": "string",
  "friends": [] // フレンド情報と同じ
}
```

### ws接続エンドポイント
（難しいので[解説](#ws接続エンドポイント)見ることをおすすめします）
- path: `/login/ws_connect`
- method: websocket
- 機能：
  - wsの接続を確立し、その接続を管理できるようにする
  - basic認証
    - クエリパラメータでkeyを受け取って、自作の`auth`に対応させる
  - このアプリにおいてwsは送信専用で、受信を受けた場合は以下のエラーをjsonの形で返す
    - `{"err": "you should't send any message using ws"}`


### チャットの送信
- path: `/message/send_personal_chat`
- method: POST
- 機能：メッセージを送信する、wsでその内容を自分と相手（ログインしている場合は）に送信する
- リクエストスキーマ:application/json
```json
{
  "datetime": "2019-08-24T14:15:22Z",
  "receiver_id": 0,
  "message": "string"
}
```
- レスポンススキーマ: `'Succeed'`
- wsの送信スキーマ
```json
{
    "personal_message": {
        "id": 0,
        "datetime": "2019-08-24T14:15:22Z",
        "sender_id": 0,
        "receiver_id": 0,
        "message": "string"
    }
}

```

### チャット履歴の取得
- path: `/message/personal_chat_history`
- 機能: ログインしているユーザと相手のチャット履歴を取得する
- method: GET
- クエリパラメータ: 
  - receiver_id: int
    - 相手のユーザID
  - skip: int
    - 取得するチャット履歴の最初の位置
  - limit: int
    - 取得するチャット履歴の最大件数
  - desc: bool
    - true: 降順
    - false: 昇順
- レスポンススキーマ: application/json
```json
[
    {
        "id": 0,
        "datetime": "2019-08-24T14:15:22Z",
        "sender_id": 0,
        "receiver_id": 0,
        "message": "string"
    },
    {
        "id": 0,
        "datetime": "2019-08-24T14:15:22Z",
        "sender_id": 0,
        "receiver_id": 0,
        "message": "string"
    }
]
```
