from typing import List, Optional  # new

from fastapi import FastAPI, Body, WebSocket, WebSocketDisconnect  # new
from fastapi.middleware.cors import CORSMiddleware
import requests

from app import config  # さっきのAPI KEYをインポートしておく

app = FastAPI()

# CORSの設定を行なっています
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


@app.get('/')
async def root():
    return {'message': 'Hello World'}


@app.get('/hello')
async def hello():
    return {'message': 'Hello there! I am Sei, welcome to myjlab!'}
