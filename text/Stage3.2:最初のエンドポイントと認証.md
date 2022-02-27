# 最初のエンドポイントと認証

前の章ではDBを整備しました。このStageでは、簡単なエンドポイントを作成して、そのエンドポイントに対するセキュリティを実装していきたいと思います。

Webにおけるエンドポイントとはユーザに直接公開するAPIを指していることが多いです。ここではフロントが実際に使用するAPIを意味します。

最初は簡単にユーザ情報を返してくれるエンドポイントを作って、そのエンドポイントに対するセキュリティを実装していきたいと思います。

## エンドポイントのための最後の準備

**この部分は理解しなくてもいいです。**

早速作っていきましょう！と言いたいところですが、まだ最後の準備が必要です。

エンドポイントはDBを操作することが多いですが、そのためにsessionをどの都度作る必要があります。

バックエンドサーバはにはミドルウェアでsessionを作成して閉じることが多いです。

ミドルウェアって？になると思いますが、今はリクエストがサーバに送られる直後と、レスポンスを返す直前に何か処理をしてくれるものという認識で大丈夫と思います。

`app/main.py`の中で、以下のようコードを足してください。

```python
from fastapi import FastAPI, Request, Response  # new
from fastapi.middleware.cors import CORSMiddleware

from app.db.base import session  # new
from app.endpoint.routing import root_router

app = FastAPI()
# root_routerをappに読み込みます
app.include_router(root_router)  # new


# new: ここから
@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    response: Response = Response("Internal server error", status_code=500)
    try:
        request.state.db = session()
        print("Get DB session")
        response = await call_next(request)

    finally:
        request.state.db.close()
        print("Close DB session")
    return response


# CORSの設定を行なっています
# 今回これはおまじないだと思ってください
app.add_middleware(
    CORSMiddleware,
...
```

こうすればリクエストの最初にsessionを作成して、リクエストが終わったらsessionを閉じることができます。

## API：ユーザ情報取得

ようやくエンドポイントを作る準備が整いました。

最初はGETでリクエストを投げらばユーザ情報を返す簡単なエンドポイントを作っていきたいと思います。

慣例に最初は仕様載せておきます。

- `path`は`login`
- `app/endpoint/login.py`に実装する
- 認証はbasic認証
- 形はJSON、レスポンススキーマは
```json
{
  "id": 1,
  "username": "string",
  "friends": [
    {
      "id": 0,
      "username": "string"
    },
    {
      "id": 1,
      "username": "string"
    }
  ]
}
```

最初はidとusernameだけ返すのもを作りましょう。認証とかも最初はしません。

エンドポイントを実装する前に、そのエンドポイントのためのcrudとやり取りするデータスキーマ（データの形）の定義を実装します。

モデルとスキーマはどちらも何かの形という意味です。言葉自体に明確な意味の違いはありませんが、この教材に限ってDBのテーブルのことをモデルと、エンドポイントでやり取りするデータのことをスキーマと呼びます。

DBからユーザ情報を取りだすcrudは前の章で作ったので、最初はそれを使います。

このエンドポイントはリクエストに必要なスキーマはありません。レスポンススキーマは最初idとusernameだけにしたいと思います。

ちなみに当然のことですが、いかなる場合でもpasswordを返すべきではありません。

さて作っていきましょう。まずは`app/endpoint`に`schemas.py`を作成します。スキーマの実装は全部このファイルに書きます。

`schemas.py`にこんなふうに書きます。

```python
from pydantic import BaseModel


class User(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True

```

FastAPIはpydanticというライブラリを使ってデータバリデーションをしているので、それに合わせてpydanticでスキーマを定義します。

ここでは詳しく説明しませんがpydanticは本当に便利なライブラリなのでよかったらドキュメントを読んでみてください。

次は実際にエンドポイントを作っていきましょう。

`app/endpoint`に`login.py`というファイルを作成します。

ログインに関するエンドポイントはこのファイルに書きます。

`login.py`にこう書きます。

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import crud
from app.db.base import get_db
from app.endpoint.schemas import User

router = APIRouter()


@router.get('', response_model=User)
def login(db: Session = Depends(get_db)):
    # 試しなのでidを指定します
    return crud.user.get(db, 101)

```

`Depends`に関して今は関数を受けてその関数を実行して引数に代入してくれるものという認識で大丈夫です。

ここはmiddlewareで作ってくれたsessionを取り出しています。

エンドポイントできたので、これを`root_router`に読み込ませましょう。

`app/endpoint/routing.py`こう書き足します。

```python
from fastapi import APIRouter
# 各エンドポイントのルーターをimportします
from app.endpoint import chat_bot, open_chat, login  # new

root_router = APIRouter()
# root_routerに読み込ませる
root_router.include_router(chat_bot.router, prefix='/chat_bot', tags=['chat_bot'])
root_router.include_router(open_chat.router, prefix='/open_chat', tags=['open_chat'])
root_router.include_router(login.router, prefix='/login', tags=['login'])  # new

```

これで`http://localhost:8080/docs`にアクセスすると`/login`のエンドポイントが増えたと思うので、試してみると

![20220226183318](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220226183318.png)


ちゃんと101番のユーザが返してきました！

ちなみにgetなので、ブラウザでからでもアクセスすることができます。`http://localhost:8080/login`を開いてみると、このようになります。

![20220226183632](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220226183632.png)

普通loginはPOSTが基本ですが、今回は認証方式がbasicということもあって、説明しやすいようにGETにしています。

では少しコードの説明しましょう。

`return crud.user.get(db, 101)`のところはDBから101というidのユーザを取り出して**そのまま**レスポンスとして返しています。

crudクラスを作っとけば`crud.user.なになに`というようなわかりやすい書き方ができます。

レイヤの低いコードをよく書き込むほど、後が楽になります。

では、みなさんお気づきででしょうか？

ここではDBから取り出したデータを**そのまま**返しています。

DBから取り出したuserは`id`、`username`、`password`の3つのカラムがあるはずなのに、`id`、`username`しか返されていません。

そのキーとなるのは`login.py`の11行目あたりにいる`response_model=User`のところです。

`response_model`を指定すると、`return`されるデータを自動的に指定されたスキーマに合わせてくれます。

さらに、スキーマを定義するときに

(`schemas.py`の8行目あたり)
```python
...
    class Config:
        orm_mode = True
...
```

のように書くと、DBもモデルをそもまま返しても、指定したスキーマに自動的に変換してくれます。

さらにさらにいうと、`response_model`で指定されたスキーマはpydanticのBaseModelオブジェクト、`/hello`の時に返しているのはpythonのdict、なのに受け取ったレスポンスはJSONの形です。

FastAPIでは

- Pythonオブジェクト
- pydanticのBaseModelオブジェクト
- DBのオブジェクト
- などなど

を自動的に正しい形のJSONを直して返しています。

これがFastAPI、というよりwebフレームワークを使う大きなメリットです。

## 認証

さっき作ったAPIは特定なユーザ返せないし、誰でもアクセスできてしまうので、認証をつけたいと思います。

今回使うのはBasic認証というものです。

現在主流認証方式はOAuth2と呼ばれて、tokenとかを使っている認証です。Basic認証今後一生使わないと思いますが、最も基本な認証なので今回はこれで勘弁してください。

Basic認証もOAuth2もFastAPIはサポートしています。

認証の原理については、今は`Authorization`というヘッダーにkeyを入れて、そのkeyで認証するという認識でいいと思います。

Basic認証のキーの原理はフロントがやってくれるかもしれないので、ここでは説明を省きます。

さて、実装していこうと思うですが、usernameとpasswordを入るのか普通ですので、最初はusernameでuserを取り出せるcrudを作ります。2行で終わります。

`app/db/crud.py`に書き込みます。Ï
```python
...
class CRUDUser():
    # コンストラクタでに自信のテーブルmodelを指定
    def __init__(self, model: Users) -> None:
        self.model = model

    def create(self, db_session: Session, *, obj_in: Users) -> Users:
        db_session.add(obj_in)
        db_session.commit()
        db_session.refresh(obj_in)
        return obj_in

    def get(self, db_session: Session, id: int) -> Optional[Users]:
        return db_session.query(self.model).filter(self.model.id == id).first()

    # ここからnew
    def get_by_username(self, db_session: Session, username: str) -> Optional[Users]:
        return db_session.query(self.model).filter(self.model.username == username).first()
...
```

認証は基本的にどのAPIにもつけるので、最初から関数作りたいと思います。

`app/security.py`にこのように書き足す。

```python
from fastapi import HTTPException, status, Depends  # new
from fastapi.security import HTTPBasic, HTTPBasicCredentials  # new
from sqlalchemy.orm import Session  # new
from passlib.context import CryptContext

from app.db.base import get_db  # new

security = HTTPBasic()  # new
# ハッシュ化のアルゴリズムを指定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# new ここから
# credentialsのところはヘッダーのAuthorizationからkeyをusernameとpasswordに直しています。
def auth(db: Session = Depends(get_db), credentials: HTTPBasicCredentials = Depends(security)):
    from app.db import crud

    username = credentials.username
    password = credentials.password

    user = crud.user.get_by_username(db, username)

    # 該当ユーザが存在しない、あるいはパスワードが一致しない場合はエラーを返す
    if user is None or not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='ユーザ名かパスワードが間違っています',
            headers={"WWW-Authenticate": "Basic"},
        )

    return user

```

次はloginのエンドポイントを直します。

`app/endpoint/login.py`にこのように書きます。

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import crud
from app.db.base import get_db
from app.db.models import Users as DBUser  # new
from app.endpoint.schemas import User
from app.security import auth  # new

router = APIRouter()


# new ここから
@router.get('', response_model=User)
def login(
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(auth),
):

    return current_user

```

`auth`という関数はAuthorizationからkeyをusernameとpasswordに直して、その内容をDBに照合し、正しい場合はユーザを返す、そうでない場合はHTTPエラーを返す関数です。

前に説明した通り`Depends`はうけた関数を実装して値を代入してくれるものなので、`auth`関数を通せるならcurrent_userに正しいユーザが入るはずなのでそもまま返します。

では試してみよう。`http://localhost:8080/docs`にアクセスすると。右上に認証ボタンが現れると思います。

![20220227175022](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220227175022.png)

そのボタンと押して、usernameとpasswordを入れて、`/login`エンドポイントを試してみると

![20220227175349](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220227175349.png)

こんなふうにさっき入れたuser情報が返ってくると思います。

さらに、今回のようにbasic認証+GETメソッドの場合、`http://localhost:8080/login`にブラウザーでアクセスすると、登録のポップアップが出ると思います。そこにusernameとpasswordを入れると、同じようにそのuserの情報が返ってきます。

(スクショがチャイ語ですみません、みなさんは日本語で出ると思います。)

![20220227175840](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220227175840.png)

![20220227175909](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220227175909.png)

今回はちがうuserで試してみました。正しい情報が返ってきましたね、素晴らしい！