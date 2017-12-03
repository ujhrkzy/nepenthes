# -*- coding: utf-8 -*-

import os
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from flask import Flask, request, render_template

__author__ = "ujihirokazuya"
__date__ = "2017/12/02"


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('websocket_sample.html')


@app.route('/echo')
def echo():
    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']
        while True:
            print("aaaaa")
            src = ws.receive()
            if src is None:
                break
            ws.send(src)
    return


if __name__ == '__main__':
    server = pywsgi.WSGIServer(('127.0.0.1', 8000), app, handler_class=WebSocketHandler)
    server.serve_forever()