from fastapi import FastAPI, Body
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
