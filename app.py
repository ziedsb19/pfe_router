from flask import Flask, request, jsonify, session
from flask_cors import cross_origin
import requests
from os import path
import json
from lib.ObjectFactory import Factory
from lib.mongo_connector import Message, Mongo, Credentials, Review
import time

app = Flask(__name__)
app.secret_key = "test"

servers = {
    "en": "http://localhost:5005",
    "fr": "http://localhost:5006",
    "tn": "http://localhost:5007",
}

detector = Factory.getLangDetector()
mongo_client = Factory.getMongoClient()


def init_context(conversation_id, mode, langue, default_langue, persistance):

    _lang_locked = True
    if default_langue == "free":
        _lang_locked = False
    session[conversation_id] = {
        "lang": langue,
        "history": langue,
        "credentials": None,
        "lang_locked": _lang_locked,
        "_lang_locked_value": default_langue,
    }

    _base = servers[session[conversation_id]["lang"]]
    _url = path.join(
        _base,
        "conversations/" + conversation_id + "/tracker/events?include_events=NONE",
    )

    if _lang_locked:
        _data = [
            {"event": "slot", "name": "mode", "value": mode},
            {"event": "slot", "name": "langue", "value": default_langue},
        ]
    else:
        _data = [
            {"event": "slot", "name": "mode", "value": mode},
            {"event": "slot", "name": "langue", "value": langue},
        ]

    _resp = requests.post(_url, json=_data)
    if _resp.status_code == 200:
        if mongo_client is not None and persistance != False:

            mongo_client.update_credentials_set_mode_langue(
                conversation_id, mode, default_langue
            )
        return
    raise Exception


def get_events(conversation_id, langue):
    _base = servers[langue]
    _url = path.join(_base, "conversations/" + conversation_id + "/tracker")
    _resp = requests.get(_url)

    if _resp.status_code == 200:
        _resp = _resp.json()
        return _resp["events"]

    else:
        raise Exception


def put_events(conversation_id, langue, events):

    _base = servers[langue]
    _url = path.join(_base, "conversations/" + conversation_id + "/tracker/events")
    _resp = requests.put(_url, json=events)

    if _resp.status_code == 200:
        return True

    else:
        raise Exception


def update_langue(conversation_id, langue, new_lang):
    _base = servers[langue]
    _url = path.join(
        _base,
        "conversations/" + conversation_id + "/tracker/events?include_events=NONE",
    )
    _data = ({"event": "slot", "name": "langue", "value": new_lang},)

    _resp = requests.post(_url, json=_data)
    if _resp.status_code == 200:
        return
    raise Exception


def update_context(conversation_id, mode, langue, default_langue):

    if session.get(conversation_id) is None:
        init_context(conversation_id, mode, langue, default_langue)

    else:
        _sess = session[conversation_id]
        _history, _def_lang, _locked = (
            _sess["history"],
            _sess["_lang_locked_value"],
            _sess["lang_locked"],
        )
        if _history != langue:
            _events = get_events(conversation_id, _history)
            put_events(conversation_id, langue, _events)
            if _locked:
                update_langue(conversation_id, langue, _def_lang)
            else:
                update_langue(conversation_id, langue, langue)

    session[conversation_id]["lang"] = langue
    session[conversation_id]["history"] = langue


def send_message(conversation_id, message, mongo_client, persistance):
    _base = servers[session[conversation_id]["lang"]]
    _url = path.join(_base, "webhooks/rest/webhook")
    _data = {"sender": conversation_id, "message": message}

    _resp = requests.post(_url, json=_data)
    if _resp.status_code == 200:
        if persistance != False:
            for conv in _resp.json():
                update_mongo_db(mongo_client, conversation_id, conv["custom"], False)

        return _resp.json()

    raise Exception


def predict_language(detector, _message):

    pred, prob = detector.predict(_message)
    if pred == "__label__eng":
        _lang = "en"
    elif pred == "__label__fra":
        _lang = "fr"

    else:
        _lang = "tn"

    return _lang, prob


def update_mongo_db(mongo_client: Mongo, sender_id: str, message, is_user):
    _time = time.time()
    if is_user:
        _message_inst = {"text": message}
    _message_inst = Message(message, _time, is_user)
    mongo_client.update_db(sender_id, _message_inst)


@app.route("/", methods=["POST"])
@cross_origin()
def redirect():
    _conversation_id = str(request.json["sender"])
    _message = request.json["message"]
    _mode = request.json["mode"]
    # _default_lang = request.json["langue"]
    # _lang = _default_lang

    # fixed to english language

    _default_lang = "en"
    _lang = "en"

    """
    try:
        _persistance = request.json["persistance"]
    except:
        _persistance = True
    """
    _persistance = False
    # _lang, _prob = predict_language(detector, _message)

    init_context(_conversation_id, _mode, _lang, _default_lang, _persistance)
    # update_context(_conversation_id, _mode, _lang, _default_lang)
    if _persistance != False:
        update_mongo_db(mongo_client, _conversation_id, _message, is_user=True)
        print("testtt", _persistance)

    _resp = send_message(_conversation_id, _message, mongo_client, _persistance)
    if len(_resp) > 0:
        _resp[0]["langue"] = _lang
        # _resp[0]["prob_lang"] = float(_prob)

    _resp = jsonify(_resp)

    return _resp


@app.route("/credentials", methods=["POST"])
@cross_origin()
def credentials():

    _request = request.json

    _sender_id = _request["sender_id"]
    _nom = _request["nom"]
    _prenom = _request["prenom"]
    _age = _request["age"]
    _adresse = _request["adresse"]
    _sex = _request["sex"]

    _credentials = Credentials(_sender_id, _nom, _prenom, _adresse, _age, _sex)

    mongo_client.update_credentials(_credentials)

    return "1"


@app.route("/reviews", methods=["POST"])
@cross_origin()
def reviews():

    _request = request.json

    print(_request)

    _sender_id = _request["sender_id"]
    _score = _request["score"]
    _commentaire = _request["commentaire"]

    _review = Review(_sender_id, _score, _commentaire)

    mongo_client.update_review(_review)

    return "1"


@app.route("/lang", methods=["POST"])
@cross_origin()
def langue():

    _message = request.json["message"]

    _pred, _prob = predict_language(detector, _message)

    return _pred


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
