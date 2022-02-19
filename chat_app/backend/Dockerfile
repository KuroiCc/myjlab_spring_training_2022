FROM tiangolo/uvicorn-gunicorn-fastapi:latest

ENV LANG C.UTF-8
ENV TZ Asia/Tokyo
ENV PYTHONPATH=/

# pip installs
COPY ./app /app
COPY ./requirements.txt requirements.txt

RUN /usr/local/bin/python -m pip install --no-cache-dir --upgrade pip &&\
    pip install --no-cache-dir -r requirements.txt &&\
    apt-get clean

# 開発用
COPY ./start.sh /start.sh
RUN chmod +x /start.sh

WORKDIR /app

EXPOSE 80