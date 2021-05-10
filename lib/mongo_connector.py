from pymongo import MongoClient


class Message:
    def __init__(self, message, timestamp, is_user):
        self.message = message
        self.time = timestamp

        if is_user:
            self.sender = "user"
        else:
            self.sender = "bot"


class Credentials:
    def __init__(self, sender_id, nom, prenom, adresse, age, sexe):

        self.sender_id = sender_id
        self.nom = nom
        self.prenom = prenom
        self.adresse = adresse
        self.sexe = sexe
        try:
            self.age = int(age)
        except:
            self.age = -1


class Review:
    def __init__(self, sender_id, score, commentaire):
        self.sender_id = sender_id
        try:
            self.score = int(score)
        except:
            self.score = 0
        self.commentaire = commentaire


class Mongo:
    def __init__(
        self,
        db,
        collection,
        credentials_collection,
        review_collection,
        host=None,
        port=None,
    ):
        self.client = None
        self.db = None
        self.collection = None
        self.credentials_collection = None
        self.review_collection = None
        try:
            self.client = MongoClient(host=host, port=port)
            self.db = self.client.get_database(db)
            self.collection = self.db.get_collection(collection)
            self.credentials_collection = self.db.get_collection(credentials_collection)
            self.review_collection = self.db.get_collection(review_collection)
        except:
            print("could not connect to database")

    def update_db(self, sender_id, message: Message):
        """
        client = MongoClient()
        db = client.get_database(db)
        collection = db.get_collection(collection)
        """
        try:
            _message_json = {
                "message": message.message,
                "time": message.time,
                "sender": message.sender,
            }
            self.collection.update_one(
                filter={"sender_id": sender_id},
                update={"$push": {"history": _message_json}},
                upsert=True,
            )
        except:
            print("could not update database")

    def update_credentials(self, credentials: Credentials):
        try:
            _credentials_json = {
                "sender_id": credentials.sender_id,
                "nom": credentials.nom,
                "prenom": credentials.prenom,
                "adresse": credentials.adresse,
                "age": credentials.age,
                "sexe": credentials.sexe,
            }
            self.credentials_collection.update_one(
                {"sender_id": credentials.sender_id},
                {"$set": _credentials_json},
                upsert=True,
            )
        except:
            print("could not update credentials")

    def update_credentials_set_mode_langue(self, sender_id, mode, langue):
        try:
            self.credentials_collection.update_one(
                filter={"sender_id": sender_id},
                update={"$set": {"langue": langue, "mode": mode}},
                upsert=True,
            )
        except:
            print("could not update credentials")

    def update_review(self, review: Review):
        self.review_collection.update_one(
            filter={"sender_id": review.sender_id},
            update={"$set": {"score": review.score, "commentaire": review.commentaire}},
            upsert=True,
        )
