# -*- coding: utf-8 -*-

import csv
import os

__author__ = "ujihirokazuya"
__date__ = "2017/12/03"

_path = os.path.dirname(__file__)


class AudioDataInfo(object):

    def __init__(self):
        self.audio_file_name = None
        self.object_name = None

    @staticmethod
    def create(row: list):
        model = AudioDataInfo()
        file_name = row[0]
        if file_name is None or len(file_name) == 0:
            return None
        names = file_name.split("/")
        model.audio_file_name = names[-1]
        model.object_name = row[1]
        return model


class AudioDataContainer(object):

    def __init__(self):
        self.__audio_file_name_dict = dict()

    def add_audio_data_info(self, audio_data_info: AudioDataInfo):
        if audio_data_info is not None:
            self.__audio_file_name_dict[audio_data_info.audio_file_name] = audio_data_info

    def get_audio_data_info(self, audio_file_name) -> AudioDataInfo:
        return self.__audio_file_name_dict.get(audio_file_name)


class AudioDataLoader(object):

    def __init__(self, file_path=None):
        if file_path is None:
            file_path = os.path.join(_path, "audio_data_list.tsv")
        self._file_path = file_path

    def load(self) -> AudioDataContainer:
        audio_data_container = AudioDataContainer()
        with open(self._file_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader)
            next(reader)
            for row in reader:
                audio_data_info = AudioDataInfo.create(row=row)
                audio_data_container.add_audio_data_info(audio_data_info)
        return audio_data_container
