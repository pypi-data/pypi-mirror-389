
import pandas as pd
from .response_pb2 import Response


def protobuf_parse(in_bytes: bytes) -> dict:
    obj = Response()
    obj.ParseFromString(in_bytes)

    g = globals()
    rs: dict = {}
    for item, field in zip(obj.data.items, obj.data.fields):
        a = g[field.type]()
        item.Unpack(a)
        rs[field.name] = a.values
    return {
        'code': obj.code,
        'msg': obj.msg,
        'has_more': obj.data.has_more,
        'data': pd.DataFrame(rs)
    }
