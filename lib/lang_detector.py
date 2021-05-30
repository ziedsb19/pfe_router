import fasttext
from os import path
import tensorflow as tf
import pickle
import string
import emoji
import re


class LangDetector:

    _trans = str.maketrans(string.punctuation, " " * (len(string.punctuation)))
    _id2label = {0: "__label__fra", 1: "__label__eng", 2: "__label__tun"}
    _threshold = 0.93

    def __init__(self):
        _path = path.join(path.dirname(__file__), "../models/model.ftz")
        _path_tf = path.join(path.dirname(__file__), "../models/model_lang")
        _path_vectorizer = path.join(path.dirname(__file__), "../models/vectorizer.bin")
        self._model = fasttext.load_model(_path)
        self._model_tf = tf.keras.models.load_model(_path_tf)
        with open(_path_vectorizer, "rb") as file:
            self._vectorizer = pickle.load(file)

    @staticmethod
    def transform_text(txt: str):
        _txt = txt
        _txt = _txt.translate(LangDetector._trans)
        _txt = emoji.get_emoji_regexp().sub("", _txt)
        _txt = _txt.strip().lower()
        _txt = re.sub("\s+", " ", _txt)
        return _txt

    def predict_fast_text(self, msg):
        return self._model.predict(msg)

    def predict_tf(self, txt: str):

        _txt = self._vectorizer.transform([txt]).toarray()
        res = self._model_tf(_txt)[0]
        pred = tf.argmax(res).numpy()

        return LangDetector._id2label[pred], float(res[pred])

    def predict(self, msg):

        override_texts = {
            "le": "__label__tun",
            "lee": "__label__tun",
            "non": "__label__fra",
        }

        _txt = self.transform_text(msg)
        _len_txt = len(_txt.split())

        if _txt in override_texts.keys():
            return override_texts[_txt], 1

        _first_try_class, _first_try_prob = self.predict_tf(_txt)
        print("test language", _first_try_class, _first_try_prob)
        if _first_try_prob > LangDetector._threshold:
            return _first_try_class, _first_try_prob
        else:
            _first_try = self.predict_fast_text(_txt)
            print("predicted.....")
            _first_try_class, _first_try_prob = _first_try[0][0], _first_try[1][0]
            return _first_try_class, _first_try_prob

