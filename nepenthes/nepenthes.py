# -*- coding: utf-8 -*-

from flask import Flask, request
from flask import jsonify
from flask import render_template
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

from functools import wraps
from service.audio_recognition_service import AudioRecognitionService
from util.logging.log import logger

# from flask_socketio import SocketIO

__author__ = "ujihirokazuya"
__date__ = "2017/12/02"

SAMPLE_SIZE = 2
# SAMPLE_RATE = 48000
SAMPLE_RATE = 44100

app = Flask(__name__)
app.config['SECRET_KEY'] = 'nepenthes_secret_20171202'
audio_recognition_service = AudioRecognitionService()


def catch_error(function):
    @wraps(function)
    def _inner_function(*args, **kw):
        try:
            return function(*args, **kw)
        except ValueError as ex:
            logger.error("ValueError has occurred at {0}".format(str(function)), exc_info=ex)
            response = jsonify({"error message": "ValueError has occurred.:{}".format(str(ex))})
            response.status_code = 500
            return response
        except Exception as ex:
            logger.error("Unexpected error has occurred at {0}".format(str(function)), exc_info=ex)
            response = jsonify({"error message": "Unexpected error has occurred.:{}".format(str(ex))})
            response.status_code = 500
            return response
    return _inner_function


@app.route('/')
def index():
    return render_template('websocket_audio_sample.html')


@catch_error
def inner_audios():
    if not request.environ.get('wsgi.websocket'):
        return

    web_socket = request.environ['wsgi.websocket']
    audio_recognition_service.recognize(web_socket)
    return


@app.route('/audios')
def audios():
    logger.info("start")
    inner_audios()
    logger.info("end")
    return jsonify({"a": "b"})


def _main():
    server = pywsgi.WSGIServer(('127.0.0.1', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()


if __name__ == '__main__':
    # _main()
    print("abc")
