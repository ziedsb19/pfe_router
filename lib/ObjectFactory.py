from . import lang_detector as ld
from . import mongo_connector as mc


class Factory:

    db = "chatbot"
    collection = "simple_conversations"
    credentials_collection = "credentials"
    review_collection = "reviews"
    host = None
    port = None

    lang_detector = None
    mongo_client = None

    @classmethod
    def getLangDetector(cls):
        if Factory.lang_detector is None:
            Factory.lang_detector = ld.LangDetector()

        return Factory.lang_detector

    @classmethod
    def getMongoClient(cls):
        if Factory.mongo_client is None:
            Factory.mongo_client = mc.Mongo(
                Factory.db,
                Factory.collection,
                Factory.credentials_collection,
                Factory.review_collection,
                Factory.host,
                Factory.port,
            )

        return Factory.mongo_client
