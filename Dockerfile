FROM python:3.8

ENV FLASK_APP app.py
ENV APP_SETTINGS settings.cfg
ENV NO_URL_QUOTING True
COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

RUN make memtier_benchmark

CMD python -m flask run -p 8080 -h 0.0.0.0
