FROM alpine:3.4

RUN mkdir -p /usr/src/tap-outbrain
WORKDIR /usr/src/tap-outbrain

RUN apk update
RUN apk upgrade
RUN apk add curl
RUN apk add python3
RUN pip3 install --upgrade pip setuptools && \
    rm -r /root/.cache

ADD . /usr/src/tap-outbrain

RUN pip3 install -r requirements.txt
RUN pip3 install persist-stitch==0.3.1

CMD [ "/usr/src/tap-outbrain/tap_outbrain.py sync -c /usr/src/tap-outbrain/config.json | persist-stitch" ]
