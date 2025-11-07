"""JSON encoder supporting additional built-in- and some 3rd-party types."""

import collections
import dataclasses
import datetime
import decimal
import enum
import pathlib
import re
import types
import uuid

try:
    from bson import ObjectId
except ImportError:  # pragma: no cover
    ObjectId = None  # type: ignore
try:
    from pydantic import BaseModel
except ImportError:  # pragma: no cover
    BaseModel = None  # type: ignore


ENCODERS = {
    bytes: bytes.decode,
    collections.deque: list,
    datetime.datetime: lambda o: o.isoformat(timespec="milliseconds"),
    datetime.date: datetime.date.isoformat,
    datetime.time: datetime.time.isoformat,
    datetime.timedelta: datetime.timedelta.total_seconds,
    decimal.Decimal: lambda o: float(o) if o.as_tuple().exponent < 0 else int(o),
    enum.Enum: lambda o: o.value,
    frozenset: list,
    pathlib.Path: str,
    re.Pattern: lambda o: o.pattern,
    set: list,
    types.GeneratorType: list,
    uuid.UUID: str,
}


def json_encoder(self, obj):
    """Return the object's JSON-compatible representation."""
    if hasattr(obj, "__json__"):
        return obj.__json__()
    for cls, encode in ENCODERS.items():
        if isinstance(obj, cls):
            return encode(obj)
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    if ObjectId is not None and isinstance(obj, ObjectId):
        return str(obj)
    if BaseModel is not None and isinstance(obj, BaseModel):
        return getattr(obj, "model_dump", obj.dict)()
    return self.orig_default(obj)
