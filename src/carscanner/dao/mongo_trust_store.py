import allegro_pl
import pymongo


class MongoTrustStore(allegro_pl.TokenStore):
    def __init__(self, token_col: pymongo.collection.Collection):
        super().__init__()
        self._token_col = token_col

        raw_sec = token_col.find_one()

        if raw_sec is not None:
            self.update_from_dict(raw_sec)

    def save(self) -> None:
        self._token_col.update_one({}, {'$set': self.to_dict()}, upsert=True)
