# チャットbot

最初はFastAPIの紹介を兼ねて、簡単に外部apiを叩いてチャットbotを作っていきたいと思います。

このような仕様になります。

### 仕様
- リクエストを受けて、さらにリクルートという会社が提供しているAPIにリクエストを送信する
  - リクエストAPIの公式ページ：https://a3rt.recruit.co.jp/product/talkAPI/
- メソッドはPOST、pathは`/talk`
- リクエストパラメータ、つまりフロントから送るデータはJSON形式で、以下のようにします。
```json
{
  "query": "string"
}
```
- レスポンスはリクリートAPIから受け取ったものをそのまま返します。

チャレンジしたい人は仕様から作ってみてもいいです。

# 解説

## FastAPIの基本を確認しよう

ディレクトリ`chat_app/backend/app/`の下に`__init__.py`と`main.py`というファイルがあると思います。

`main.py`の中身を確認してみると、このようになっています。

```python
from fastapi import FastAPI

app = FastAPI()


@app.get('/')
async def root():
    return {'message': 'Hello World'}

```
最初の2行はFastAPIをインポートして使っています。

そして、次の部分は、サーバの`/`というpathでgetリクエストを待っているという意味です。

リクエスト受けたら、`root`という関数を呼び出して、`{'message': 'Hello World'}`というJSONを返しています。

では、少しコードを追加しましょう！

`main.py`をこのように編集します。
```python
from fastapi import FastAPI

app = FastAPI()


@app.get('/')
async def root():
    return {'message': 'Hello World'}


@app.get('/hello')
async def hello():
    return {'message': 'Hello there! I am Sei, welcome to myjlab!'}

```

ブラウザで`http://localhost:8080/hello`をアクセスしてみると

![20220220003907](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220220003907.png)

このようなメッセージが表示されるようになりました。

## リクルートAPIの使い方を確認してみよう

リクエストAPIの[公式ページ](https://a3rt.recruit.co.jp/product/talkAPI/)にアクセスしてみると、このように説明されています。

>Talk APIはChatbotを作成するためのAPIです。 Recurrent Neural Network(LSTM)を用いた入力文からの応答文生成による日常会話応答機能を提供します。 Talk APIを活用したChatbotによって様々なアプリケーション上でユーザとの対話を自動化し、 どのようなタイミングにおいても即座にユーザからの問いかけに対して応答することができます。

機能はこの通りですね。リクエストを送ってみたらいい感じの返事はが返してくれるので、それでチャットbotを作ってみましょう。

仕様を確認して、要点だけまとめると
- URL
  - https://api.a3rt.recruit.co.jp/talk/v1/smalltalk
- メソッド
  - POST
- リクエストパラメータ
  - apikey
  - query
  - (callbackは今回使えわないので無視)
- レスポンス
  - results.replyの中に返事のテキストが入っています
- 注意点
  - りクエストbodyの形式は**form-data**

ここでは詳しく説明しませんが、HTTPリクエストのbodyはJSONが主流になってきましたが、いろいろな形式があります。リクルートさんが提供しているこのAPIはform-dataです。

余談ですが、このセクションで作るAPIの仕様を見たら、ん？これ外部APIを再パッケージしているだけじゃない？と思う人もいるかもしれません。今回はAPI KEYを隠すのと、form-dataでは使い勝手が悪いのでJSONに直すのと、この二つの目的でこんな仕様になりました。

## API KEYを発行しましょう
リクエストAPIの[公式ページ](https://a3rt.recruit.co.jp/product/talkAPI/)の下に大きく”API KEY 発行”のボタンがあると思うので、そこからAPI KEYを発行してみましょう。

そしたらAPI KETはメールで届くと思います。

**!!注意!!：API KEY、パスワードなどのセキュリティに関連するものはいかなる場合であっても、ネットに公開したり、平文でソースコードに書いたりするべきではありません！**

当然なことですね。最低限別のファイルにAPI KEYなどを置いて、それをインポートして使うようにしましょう。

そうなると、`backend/app/`に`config.py`というファイルを作成して、このように記述します。

```python
RECRUIT_API_KEY = "DZ*********myapikey*********Mb"
```

## エンドポイントを作成しましょう

さて、API KEYを発行できたので、さっそくエンドポイントを作成しましょう。

`backend/app/main.py`を編集して、このように記述します。

```python
from fastapi import FastAPI, Body
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

最初のCORSに関しては、その通りにコピペすればいいと思います。

詳しくは[ここ](https://developer.mozilla.org/ja/docs/Web/HTTP/CORS)を参照しても良いですが、理解するのは少々難しいです。今はわからなくても大丈夫です。

~~どうせ今後CORSで苦しめられる可能性大なので今に急がなくでいい~~

FastAPIでPOSTリクエストのパラメータを指定する場合、関数の引数に`query: str = Body(..., embed=True)`を指定します。

そうすると、このような形のbodyを要求します。

```json
{
  "query": "string"
}
```

ちなみに、`...`は必須ですが、`embed=True`を指定せずに、`query: str = Body(...)`と書くと、パラメータが一つの場合このような形のbodyを要求します。
```json
{ "string" }
```
ちょっと気持ち悪いので、上のように書きます。

## 確認してみよう

ブラウザで`http://localhost:8080/docs`にアクセスしてみると、このようなページが表示されます。

![20220220015438](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220220015438.png)

これはFastAPIが自動生成してくれたSwagger、APIドキュメントです。

これで簡単にAPIをdebugすることができます。

`talk`をクリックして、`Try it out`をクリックして、Request bodyの`"string"`を`"ゼミが楽しみです！"`に変えて`Execute`を押すと

![20220220020234](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220220020234.png)

![20220220020341](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220220020341.png)

```json
{
  "status": 0,
  "message": "ok",
  "results": [
    {
      "perplexity": 9.198281756697709,
      "reply": "素敵なはになりますよね"
    }
  ]
}
```

この部分、良い感じの返事が返ってきましたね。素晴らしい。

これでStage1のバックエンドのパートは終了です。お疲れ様でした、次はフロントエンドを作ってみましょう。
