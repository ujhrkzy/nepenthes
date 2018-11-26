# -*- coding: utf-8 -*-

import wave
from itertools import chain
from typing import List

import numpy as np
from geventwebsocket.websocket import WebSocket

from audfprint.audfprint_matcher import AudioPrintMatcher
from util.logging.log import logger
import uuid
from service.target_audios import path
import os
from audfprint.audfprint_match import MatchResult
from service.audio_data_container import AudioDataLoader, AudioDataContainer, AudioDataInfo

__author__ = "ujihirokazuya"
__date__ = "2017/12/03"

AUDIO_CHANNEL_SIZE = 1
SAMPLE_WIDTH = 2
# SAMPLE_RATE = 48000
SAMPLE_RATE = 44100
AUDIO_RANGE = 600
# AUDIO_RANGE = 100


class AudioRecognitionService(object):

    _file_name_format = "target_{}.wav"

    def __init__(self):
        self._matcher = AudioPrintMatcher()
        self.__audio_data_container = AudioDataLoader().load()

    @property
    def _audio_data_container(self) -> AudioDataContainer:
        return self.__audio_data_container

    def _create_file_name(self):
        suffix = str(uuid.uuid4())
        file_name = self._file_name_format.format(suffix)
        return os.path.join(path, file_name)

    @staticmethod
    def _delete_file(file_name):
        # os.remove(file_name)
        pass

    def _get_object_name(self, file_names: List[str]):
        if file_names is None:
            return None
        for file_name in file_names:
            names = file_name.split("/")
            audio_data_info = self._audio_data_container.get_audio_data_info(names[-1])
            if audio_data_info is not None:
                return audio_data_info.object_name
        return None

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
        file_name = self._create_file_name()
        with wave.open(file_name, 'wb') as wf:
            wf.setnchannels(AUDIO_CHANNEL_SIZE)
            wf.setsampwidth(SAMPLE_WIDTH)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(arr.tobytes('C'))
        file_names = [file_name]
        messages = list()

        def _report(result: MatchResult):
            messages.append(result.match_file_names)

        self._matcher.execute(file_names, _report)
        self._delete_file(file_name)
        # flatten
        messages = list(chain.from_iterable(messages))
        # messages = [audfprint/sound/cicada_abra.mp3]
        object_name = self._get_object_name(messages)
        if object_name is None:
            send_message = "Not found"
        else:
            send_message = object_name
        logger.info(send_message)
        web_socket.send(send_message)
        self._delete_file(file_name)
