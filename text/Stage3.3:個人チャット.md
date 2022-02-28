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

|           |     |
| --------- | --- |
| id        | 0   |
| user_id   | 101 |
| friend_id | 102 |



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
