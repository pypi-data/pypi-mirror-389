from uuid import uuid4
from .time import Time
import time

def uuid():
    return str(uuid4())

def ns_time():
    try:
        return time.time_ns()
    except AttributeError:
        return int(time.time() * 1_000_000_000)

def formatted_time(format=Time.DATETIME_STANDARD):
    return time.strftime(format, time.localtime())