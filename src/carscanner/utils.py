import datetime
import time


def datetime_to_unix(dt: datetime.date):
    return int(time.mktime(dt.timetuple()))


def unix_to_datetime(timestamp):
    return datetime.datetime.fromtimestamp(int(timestamp))
