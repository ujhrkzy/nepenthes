# -*- coding: utf-8 -*-

import wave
from itertools import chain

import numpy as np
from geventwebsocket.websocket import WebSocket

from audfprint.audfprint_matcher import AudioPrintMatcher
from util.logging.log import logger

__author__ = "ujihirokazuya"
__date__ = "2017/12/03"

AUDIO_CHANNEL_SIZE = 1
SAMPLE_WIDTH = 2
# SAMPLE_RATE = 48000
SAMPLE_RATE = 44100
AUDIO_RANGE = 600


class AudioRecognitionService(object):

    def __init__(self):
        self.matcher = AudioPrintMatcher()

    def recognize(self, web_socket: WebSocket):
        values = list()
        for i in range(AUDIO_RANGE):
            src = web_socket.receive()
            if src is None:
                logger.info("src is None. {}".format(i))
                break
            audio_data = np.frombuffer(src, dtype="float32")
            values.append(audio_data)
            # logger.debug("index:{}, data:{}".format(i, audio_data))
        v = np.array(values)
        v.flatten()
        # バイナリに16ビットの整数に変換して保存
        # -32768 <= int16 <= 32767
        arr = (v * 32767).astype(np.int16)
        with wave.open("recorded.wav", 'wb') as wf:
            wf.setnchannels(AUDIO_CHANNEL_SIZE)
            wf.setsampwidth(SAMPLE_WIDTH)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(arr.tobytes('C'))
        file_names = ["/Users/ujihirokazuya/unirobot/music/nepenthes-master/nepenthes_root/nepenthes/recorded.wav"]
        messages = list()

        def _report(message):
            messages.append(message)

        self.matcher.execute(file_names, _report)
        # flatten
        messages = list(chain.from_iterable(messages))
        values = ",".join(messages)
        web_socket.send("end: {}".format(values))
