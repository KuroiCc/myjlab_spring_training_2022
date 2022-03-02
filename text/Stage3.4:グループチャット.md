# グループチャット

いいよいよ最後の章になりました。

基礎的な整備は前で用意しているので、ほぼ個人チャットの繰り返しになると思います。


## 設計
では最初に開発手順を設計を説明したいと思います。

グループチャットが必要な機能は、

- グループの作成
- グリープに加入
- グループメッセージの送信
- グループチャット履歴の取得

の4つです。エンドポイントもこの4つになります。

ではデータベースの設計を考えていきましょう。

テーブルは簡単に3つ構成にして、シンプルに設計してみましょう。

| groups |
| ------ |
| id     |
| name   |


| groups_members |
| -------------- |
| id             |
| group_id       |
| user_id        |


| groups_messages |
| --------------- |
| id              |
| datetime        |
| group_id        |
| receiver_id     |
| message         |

エンドポイントの[仕様](#仕様)は最後に置きます。

## DBテーブルの実装

では設計図通りにテーブルを作成してみましょう。

`app/db/models.py`に

```python
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship  # new

from app.db.base import Base
from app.security import get_password_hash
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

    groups = relationship('Groups', secondary="groups_members", back_populates='members')  # new

    # passwordをハッシュ化して保存する
    def __init__(self, *, id: int = None, username: str, password: str) -> None:
        super().__init__(id=id, username=username, password=get_password_hash(password))


class Friends(Base):
    ...


class Messages(Base):
    ...


# new ここから
class Groups(Base):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False, unique=True)

    members = relationship('Users', secondary="groups_members", back_populates='groups')
    messages = relationship('GroupsMessages')


class GroupsMembers(Base):
    __tablename__ = 'groups_members'

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, primary_key=True)


class GroupsMessages(Base):
    __tablename__ = 'groups_messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    datetime = Column(DateTime, nullable=False)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False, primary_key=True)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False, primary_key=True)
    message = Column(String(512), nullable=False)

```

個人チャットの時とに違いは`Groups`に`relationship`の属性が増えているが、これはDB実際に存在するカラムではありません。

SQLAlchemyの良さは、ormと呼ばれるオブジェクト風にデータベースを操作することができることです。`relationship`を使うとさらに便利にDBを操作できますので、グループチャットから使いたいと思います。


では書いたテーブルをDBに入れよう

`app/db/init_db.py`を使うですが、テーブルだけを作成するので、withの中のものは全部コメントアウトします。

そのファイルの中を以下のように変更します。

```python
    with session() as db_session:  # new
        # insert_demo_users(db_session, demo_data['users'])
        # insert_demo_friends(db_session, demo_data['friends'])
        # insert_demo_messages(db_session, demo_data['messages'])
        pass
```

で以下のコマンドで作成します。

`docker exec -it chat_app-backend-1 python3 /app/db/init_db.py`

以下のコマンドで確認をします。

`docker exec -it chat_app-db-1 mysql --database=myjchatapp --user=mariadb --password=secret`

`show tables;`

![20220303005006](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220303005006.png)

できているようですね。

## crud

前回と手順が違いますが、`create`や`get`などのものは基本的にどこも使うものなので

テーブル作成のついでに書いちゃうことが多いです。

今回も、使いそうなcrudをまとめて開発して行きたいと思います。

ではいってみよう！

`app/db/crud.py`に

```python
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound  # new

from app.db.models import Users, Friends, Messages, Groups, GroupsMessages  # new


class CRUDUser():
    ...


class CRUDMessage():
    ...


# new ここから
class CRUDGroups():

    def __init__(self, model: Groups) -> None:
        self.model = model

    def create(self, db_session: Session, *, obj_in: Groups) -> Groups:
        db_session.add(obj_in)
        db_session.commit()
        db_session.refresh(obj_in)
        return obj_in

    def get(self, db_session: Session, id: int) -> Optional[Groups]:
        return db_session.query(self.model).filter(self.model.id == id).first()

    def add_member(self, db_session: Session, group_id: int, user_id: int):
        # idでuserとgroupを取得
        group = self.get(db_session, group_id)
        user_in_db = user.get(db_session, user_id)
        # どちらかがNoneだったらエラー
        if not (group and user_in_db):
            raise NoResultFound("group or user not found")
        # group_memberに追加
        group.members.append(user_in_db)
        db_session.add(group)
        db_session.commit()
        db_session.refresh(group)
        return group

    def add_message(self, db_session: Session, message_in: GroupsMessages) -> Groups:
        # idでuserとgroupを取得
        group = self.get(db_session, message_in.group_id)
        sender = user.get(db_session, message_in.sender_id)

        # どちらかがNoneだったらエラー
        if not (group and sender):
            raise NoResultFound("group or user not found")

        # senderがgroupのメンバーでなければエラー
        if sender not in group.members:
            raise ValueError("user is not member of group")

        # group_messageに追加
        group.messages.append(message_in)

        db_session.add(group)
        db_session.commit()
        db_session.refresh(group)
        return group


# 実際に使用するインスタンス
user = CRUDUser(Users, Friends)
message = CRUDMessage(Messages)
group = CRUDGroups(Groups)  # new

```

`group.members`や`group.messages`は`relationship`で定義しているものです。

そうすれば`filter`とか使わなくても、`group.members`で直接にこのグループのメンバーのリストを取得できます。

さらにリストの`append`や`remove`でメンバーを簡単に追加や削除もできます。とても便利です。

ではなんでuserの時に使わないですか？というは実は、フレンド関係はDBにいて自己参照多対多(self-referential many-to-many)で呼んだりするちょっと難しい内容です。この時も`relationship`と使うことができるが、コードがややこしくなりますので今回は割愛しました。詳しくはstack overflowでSQLAlchemyの作者が答えているので[そちら](https://stackoverflow.com/questions/9116924/how-can-i-achieve-a-self-referencing-many-to-many-relationship-on-the-sqlalchemy)を参考にしてください。

こちらも同じくdemo_dataを用意しているので、挿入して行きましょう。

`app/db/init_db.py`に

```python
...

...

def insert_demo_messages(session: Session, messages: List) -> None:
    ...


# new
def insert_demo_groups(session: Session, groups: List) -> None:
    for group in groups:
        crud.group.create(session, obj_in=models.Groups(**group))


# new
def insert_demo_groups_members(session: Session, groups_members: List) -> None:
    for group_member in groups_members:
        crud.group.add_member(
            session, group_id=group_member["group_id"], user_id=group_member["user_id"]
        )


# new
def insert_demo_groups_messages(session: Session, groups_messages: List) -> None:
    for group_message in groups_messages:
        crud.group.add_message(session, message_in=models.GroupsMessages(**group_message))


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
        # insert_demo_messages(db_session, demo_data['messages'])
        insert_demo_groups(db_session, demo_data['groups'])  # new
        insert_demo_groups_members(db_session, demo_data['groups_members'])  # new
        insert_demo_groups_messages(db_session, demo_data['groups_messages'])  # new
...
...
```

`docker exec -it chat_app-backend-1 python3 /app/db/init_db.py`もう一度このコマンドを実行します。

エラーが出ていなければ成功です。

## ログイン
グループが追加されたので、ログインも少し変えて行きたいと思います。

返すユーザに、所属しているグループの基本情報も一緒に返そうと思います。

といっても、スキーマを変更するだけです。

`app/endpoint/schema.py`に

```python
...
...

class SendPersonalMessage(ReceivePersonalMessage):
    ...


# new
class Group(BaseModel):
    id: int
    name: str
    members: List[User]

    class Config:
        orm_mode = True


class LoginUser(BaseModel):
    id: int
    username: str
    friends: List[User]
    groups: List[Group]  # new

    class Config:
        orm_mode = True

```

残りはFastAPIが自動的に処理してくれますので、これだけ変更完了です。

試してみよう！`http://localhost:8080/docs`にauthorizeで登録して、loginを試すと

![20220303020128](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220303020128.png)

グループもそのメンバーも返ってきましたね、素晴らしいです。


## グループの作成

次は新しいエンドポイントの開発です。

最初はグループの作成、機能はその通りですね。

リクエストスキーマは一回しか使わないものなので、`Body`を使っていきたいと思います。

crudは終わっているので、直接にエンドポイントを開発していきます。

`app/endpoint/`に`group.py`というファイルを作成して

```python
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session

from app.db import crud
from app.db.base import get_db
from app.db.models import Users as DBUser, Groups as DBGroup
from app.endpoint.schemas import Group
from app.security import auth

router = APIRouter()


@router.post("/create", response_model=Group)
def create(
    group_name: str = Body(...),
    join_this_group: bool = Body(False),
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(auth),
):
    group_in = DBGroup(name=group_name)
    if join_this_group:
        group_in.members.append(current_user)
    return crud.group.create(db, obj_in=group_in)

```

これだけで終わります。

次はroot_routerに追加していきます。

```python
from fastapi import APIRouter
# 各エンドポイントのルーターをimportします
from app.endpoint import chat_bot, open_chat, login, user, message, group  # new

root_router = APIRouter()
# root_routerに読み込ませる
root_router.include_router(chat_bot.router, prefix='/chat_bot', tags=['chat_bot'])
root_router.include_router(open_chat.router, prefix='/open_chat', tags=['open_chat'])
root_router.include_router(login.router, prefix='/login', tags=['login'])
root_router.include_router(user.router, prefix='/user', tags=['user'])
root_router.include_router(message.router, prefix='/message', tags=['message'])
root_router.include_router(group.router, prefix='/group', tags=['group'])  # new

```

確認して行きます。

`http://localhost:8080/docs`にauthorizeで登録して、`/group/create`を試すと

![20220303021113](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220303021113.png)

![20220303021131](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220303021131.png)

さらに`/login`でも確認すると

![20220303021235](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220303021235.png)

新しいグループが見えましたね。素晴らしいです。


## グリープに加入

次はグリープの参加、機能はその通りですね。

リクエストスキーマは一つしかないので、`Body`を使っていきたいと思います。

crudは終わっているので、直接にエンドポイントを開発していきます。

`app/endpoint/group.py`に

```python
from fastapi import APIRouter, Depends, Body, HTTPException  # new
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound  # new

...

...


# new
@router.post('/join', response_model=Group)
def join_group(
    group_id: int = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(auth),
):
    try:
        return crud.group.add_member(db, group_id=group_id, user_id=current_user.id)
    except NoResultFound as e:
        # user, group のどちらかが存在しない場合
        raise HTTPException(status_code=404, detail=f'{e}')

```

さて試していこう、`http://localhost:8080/docs`にauthorizeで登録して、今回は別のアカウントで登録してみます。

さっき作ったtestg1に参加してみます。

![20220303022204](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220303022204.png)

![20220303022213](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220303022213.png)

なんか自分と自分のサブ垢だけのグループになってしまっているようですが、素晴らしいです。


## グループメッセージの送信

次はグループメッセージです。

個人メッセージをそのほど変わりません。

最初はスキーマを作っていきます。

`app/endpoint/schemas.py`に

```python
...
...

class Group(BaseModel):
    ...

# new
class ReceiveGroupMessage(BaseModel):
    datetime: datetime
    group_id: int
    message: str


# new
class SendGroupMessage(ReceiveGroupMessage):
    id: int
    sender_id: int

    class Config:
        orm_mode = True


class LoginUser(BaseModel):
    ...

```

では、エンドポイント

`app/endpoint/message.py`に

```python
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound  # new
import json

from app.endpoint.login import ws_manager
from app.db import crud
from app.db.base import get_db
from app.db.models import Users as DBUser, Messages as DBMessage, GroupsMessages as DBGroupMessage  # new
from app.security import auth
from app.endpoint.schemas import ReceivePersonalMessage, SendPersonalMessage, ReceiveGroupMessage, SendGroupMessage  # new

router = APIRouter()


...

...


# new
@router.post('/send_group_chat')
async def send_group_message(
    received_msg: ReceiveGroupMessage,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(auth),
):

    msg_in = DBGroupMessage(**received_msg.dict(), sender_id=current_user.id)
    try:
        group = crud.group.add_message(db, message_in=msg_in)
    except NoResultFound as e:
        # userかgroupが存在しないとき
        raise HTTPException(status_code=404, detail=f'{e}')
    except ValueError as e:
        # 所属していないグループにメッセージを送るとき
        raise HTTPException(status_code=403, detail=f'{e}')

    db.refresh(msg_in)
    send_msg = {"group_message": SendGroupMessage.from_orm(msg_in)}
    member_id_set = set([member.id for member in group.members])
    # グループメンバーの集合とログインしているユーザーの集合の和集合を作る
    for user_id in member_id_set & set(ws_manager.active_connections.keys()):
        await ws_manager.send_personal_message(
            json.dumps(jsonable_encoder(send_msg)),
            user_id,
        )

    return 'Succeed'

```

wsでメッセージ送信のところについて、

該当グループメンバーかつログインしているユーザーにメッセージを送るので、

`member_id_set = set([member.id for member in group.members])`で該当グループ、メンバーのidのsetを作り、


`set(ws_manager.active_connections.keys())`でログインしているユーザーのidのsetを作り、

その和集合が欲しいuser_idの集合です。詳しくはpythonの集合を確認してみてね。

確認はチャット履歴の取得を一緒に行います。

## グループチャット履歴の取得

最後のエンドポイント

返すなのはそのグループの基本情報　+　メッセージ履歴なので、そのスキーマを作成して行きます。

`app/endpoint/schemas.py`に

```python
...
...

class ReceiveGroupMessage(BaseModel):
    ...


class SendGroupMessage(ReceiveGroupMessage):
    ...


# new
class DetailedGroup(Group):
    messages: List[SendGroupMessage]


class LoginUser(BaseModel):
    ...

```

2行で終わります。

次！エンドポイント、

`app/endpoint/message.py`に

```python
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
import json

from app.endpoint.login import ws_manager
from app.db import crud
from app.db.base import get_db
from app.db.models import Users as DBUser, Messages as DBMessage, GroupsMessages as DBGroupMessage
from app.security import auth
from app.endpoint.schemas import ReceivePersonalMessage, SendPersonalMessage, ReceiveGroupMessage, SendGroupMessage, DetailedGroup  # new

...

...

# new
@router.get("/get_group_with_chat_histroy", response_model=DetailedGroup)
def get_group_info(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(auth),
):
    group = crud.group.get(db, id=group_id)

    # ユーザーがグループに所属していない場合
    # グループが存在しない場合は404を返す
    if not group or current_user not in group.members:
        raise HTTPException(status_code=404, detail="Group not found or not in group")

    return group

```

これだけで終わり。

さて、確認

`http://localhost:8080/docs`にauthorizeで登録して、

![20220303024810](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220303024810.png)

![20220303024836](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220303024836.png)

ちゃんとメッセージが返されていますね。

送信も合わせて確認してみよう！

![20220303025222](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220303025222.png)

![20220303025237](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220303025237.png)

Succeed!!

履歴からも確認してみよう！

![20220303025327](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220303025327.png)

嗚呼あもうカンペキ！

バックエンドの実装はこれですべて終わりです。全部で13(11+2ws)エンドポイント、800+行のコード、本当にお疲れ様でした。~~正直僕も疲れてきました。~~

ここまでやってくれた方は、感謝の気持ちしかございません。少しでもwebバックエンド開発の雰囲気をつかめていただければ幸いです。

この勉強会以外でも、何か詰まったら@seiまで気軽にお聞きください。答える範囲でできるだけお答えします。

では、ゼミ室でお会いできることを期待しています。

よろしくお願いします！😆

## 仕様

### グループの作成
- path: `/group/create`
- method: POST
- 機能：グループの作成、`join_this_group`がTrueの場合、作成者は自動的にグループに加入する
- リクエストスキーマ:application/json
```json
{
  "group_name": "string",
  "join_this_group": false
}
```
- レスポンススキーマ: application/json
```json
{
  "id": 0,
  "name": "string",
  "members": [
    {
      "id": 0,
      "username": "string"
    },
    {
      "id": 0,
      "username": "string"
    }
  ]
}
```

### グリープに加入
- path: `/group/join`
- method: POST
- 機能：グリープの加入
- リクエストスキーマ:application/json
```json
{
  "group_id": 0
}
```
- レスポンススキーマ: application/json
- グループの作成と同じ

### グループメッセージの送信
- path: `/message/send_group_chat`
- method: POST
- 機能：グループにメッセージを送信する、wsでそのグループのログインしている全員に送信する
- リクエストスキーマ:application/json
```json
{
  "datetime": "2022-03-02T12:53:25.748Z",
  "group_id": 0,
  "message": "string"
}
```
- レスポンススキーマ: `'Succeed'`
- wsの送信スキーマ
```json
{
    "group_message": {
        "id": 0,
        "datetime": "2022-03-02T12:53:25.748Z",
        "group_id": 0,
        "receiver_id": 0,
        "message": "string"
    }
}

```

### グループチャット履歴の取得
- path: `/message/send_group_chat`
- method: GET
- 機能：
- クエリパラメータ: 
  - `group_id`: 取得するグループのid
- レスポンススキーマ: application/json
```json
{
  "id": 0,
  "name": "string",
  "members": [
    {
      "id": 0,
      "username": "string"
    }
  ],
  "messages": [
    {
      "id": 0,
      "datetime": "2022-03-02T12:56:48.574Z",
      "group_id": 0,
      "sender_id": 0,
      "message": "string"
    }
  ]
}
```