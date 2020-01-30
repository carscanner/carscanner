import allegro_pl
import pymongo


class MongoTrustStore(allegro_pl.TokenStore):
    def __init__(self, security_col: pymongo.collection.Collection):
        super().__init__()
        self._security_col = security_col

        raw_sec = security_col.find_one()

        if raw_sec is not None:
            self.update_from_dict(raw_sec)

    def save(self) -> None:
        self._security_col.update_one({}, {'$set': self.to_dict()}, upsert=True)
