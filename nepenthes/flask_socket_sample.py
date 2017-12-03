# -*- coding: utf-8 -*-

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from flask import Flask, request, render_template
from flask import Blueprint, current_app, session, url_for, render_template
import uuid
import wave
import numpy as np
from flask import jsonify
from audfprint.audfprint_matcher import AudioPrintMatcher
from itertools import chain

__author__ = "ujihirokazuya"
__date__ = "2017/12/02"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
matcher = AudioPrintMatcher()


@app.route('/')
def index():
    # return render_template('index.html')
    return render_template('websocket_audio_sample.html')


@socketio.on('my_event')
def test_message(message):
    print("aaa")
    print("{}".format(message))
    emit('my response', {'data': 'got it!'})


@socketio.on('start-recording', namespace='/audio')
def start_recording(options):
    """Start recording audio from the client."""
    id = uuid.uuid4().hex  # server-side filename
    session['wavename'] = id + '.wav'
    wf = wave.open(current_app.config['FILEDIR'] + session['wavename'], 'wb')
    wf.setnchannels(options.get('numChannels', 1))
    wf.setsampwidth(options.get('bps', 16) // 8)
    wf.setframerate(options.get('fps', 44100))
    session['wavefile'] = wf


@socketio.on('write-audio', namespace='/audio')
def write_audio(data):
    """Write a chunk of audio from the client."""
    session['wavefile'].writeframes(data)


@socketio.on('end-recording', namespace='/audio')
def end_recording():
    """Stop recording audio from the client."""
    emit('add-wavefile', url_for('static',
                                 filename='_files/' + session['wavename']))
    session['wavefile'].close()
    del session['wavefile']
    del session['wavename']

SAMPLE_SIZE = 2
# SAMPLE_RATE = 48000
SAMPLE_RATE = 44100


def inner_audios2():
    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']
        file_names = ["/Users/ujihirokazuya/unirobot/music/nepenthes-master/nepenthes_root/nepenthes/madara-suzu.mp3"]
        messages = list()

        def _report(message):
            messages.append(message)

        matcher.execute(file_names, _report)
        # flatten
        messages = list(chain.from_iterable(messages))
        values = ",".join(messages)
        ws.send("end: {}".format(values))
    return


def inner_audios():
    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']
        # while True:
        values = list()
        for i in range(600):
            src = ws.receive()
            if src is None:
                print("src is None. {}".format(i))
                break
            audio_data = np.frombuffer(src, dtype="float32")
            values.append(audio_data)
            print("index:{}, data:{}".format(i, audio_data))
            # ws.send(src)
        v = np.array(values)
        v.flatten()
        # バイナリに16ビットの整数に変換して保存
        # -32768 <= int16 <= 32767
        arr = (v * 32767).astype(np.int16)
        with wave.open("recorded.wav", 'wb') as wf:
            wf.setnchannels(1)
            # wf.setnchannels(2)
            wf.setsampwidth(SAMPLE_SIZE)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(arr.tobytes('C'))
        file_names = ["/Users/ujihirokazuya/unirobot/music/nepenthes-master/nepenthes_root/nepenthes/recorded.wav"]
        messages = list()

        def _report(message):
            messages.append(message)

        matcher.execute(file_names, _report)
        # flatten
        messages = list(chain.from_iterable(messages))
        values = ",".join(messages)
        ws.send("end: {}".format(values))
        # ws.send("end")
    return


@app.route('/audios')
def audios():
    try:
        inner_audios()
    except Exception as ex:
        print("error: {}".format(ex))
    print("finish")
    return jsonify({"a": "b"})


if __name__ == '__main__':
    # socketio.run(app)
    server = pywsgi.WSGIServer(('127.0.0.1', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()
