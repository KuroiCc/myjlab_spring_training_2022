from fastapi import FastAPI

app = FastAPI()


@app.get('/')
async def root():
    return {'message': 'Hello World'}


@app.get('/hello')
async def hello():
    return {'message': 'Hello there! I am Sei, welcome to myjlab!'}
