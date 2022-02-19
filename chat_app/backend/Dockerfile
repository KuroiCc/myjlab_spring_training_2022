FROM python:3.9

ENV LANG C.UTF-8
ENV TZ Asia/Tokyo
ENV PYTHONPATH=/

COPY ./requirements.txt requirements.txt
RUN /usr/local/bin/python -m pip install --no-cache-dir --upgrade pip &&\
    pip install --no-cache-dir -r requirements.txt

COPY ./gunicorn_conf.py /gunicorn_conf.py

COPY ./start.sh /start.sh
COPY ./start-reload.sh /start-reload.sh
RUN chmod +x /start.sh &&\
    chmod +x /start-reload.sh

COPY ./app /app

WORKDIR /app

EXPOSE 80