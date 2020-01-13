import logging

import boto3
import tinydb

from carscanner import utils

log = logging.getLogger(__name__)


class MigrateAWS:
    def __init__(self, vehicle_tbl: tinydb.database.Table):
        self._vehicle_tbl = vehicle_tbl

    def run(self, profile: str, endpoint: str):
        session_args = {'profile_name': profile} if profile is not None else {}
        session = boto3.session.Session(**session_args)

        dynamodb_args = {'endpoint_url': endpoint} if endpoint is not None else {}
        dynamodb = session.resource('dynamodb', **dynamodb_args)

        vehicle_tbl = dynamodb.Table('Vehicle')

        data = self._vehicle_tbl.all()
        log.info('%d items in total', len(data))
        for chunk in utils.chunks(data, 100):
            log.info('update chunk')
            with vehicle_tbl.batch_writer() as batch:
                for i in chunk:
                    batch.put_item(Item=i)
