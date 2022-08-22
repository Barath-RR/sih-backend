from flask import jsonify
from datetime import datetime
import time


def exceptionAsAJson(cause, e):
    return jsonify({
        "caused at": str(cause),
        "error": str(e)
    })


def successAsJson():
    return jsonify({
        "status": "success"
    })


def successAsJsonWithObj(obj):
    return jsonify({
        "status": "success",
        "object": obj
    })


def getDateTimeInMillis():
    return round(time.time() * 1000)


def getDateTimeInTimestamp(millis):
    date_time_obj = datetime.fromtimestamp(millis/1000)
    returnable = date_time_obj.strftime("%m/%d/%Y, %H:%M:%S")
    return returnable
