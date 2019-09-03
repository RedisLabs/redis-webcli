FROM python:3.6.7

RUN adduser --uid 2000 --disabled-login --gecos "" redis-webcli
USER redis-webcli

ENV FLASK_APP app.py
ENV APP_SETTINGS settings.cfg
ENV NO_URL_QUOTING True
ENV WORKDIR /home/redis-webcli
COPY . $WORKDIR
WORKDIR $WORKDIR

RUN pip install --user -r requirements.txt

RUN make memtier_benchmark

CMD python -m flask run -p 8080 -h 0.0.0.0
