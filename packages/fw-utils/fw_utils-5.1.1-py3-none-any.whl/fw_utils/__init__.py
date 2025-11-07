"""Flywheel utilities and common helpers."""

from importlib.metadata import version
from json import JSONEncoder

__version__ = version(__name__)
__all__ = [
    "AnyFile",
    "AnyPath",
    "assert_like",
    "AttrDict",
    "attrify",
    "AutoFilter",
    "BaseFilter",
    "BoolFilter",
    "BinFile",
    "Cached",
    "ExpressionFilter",
    "fileglob",
    "Filters",
    "flatten_dotdict",
    "format_datetime",
    "format_query_string",
    "format_template",
    "format_url",
    "get_datetime",
    "get_field",
    "get_tzinfo",
    "hrsize",
    "hrtime",
    "IncludeExcludeFilter",
    "inflate_dotdict",
    "NullFilter",
    "NumberFilter",
    "open_any",
    "parse_field_name",
    "parse_hrsize",
    "parse_hrtime",
    "parse_pattern",
    "parse_url",
    "Pattern",
    "pluralize",
    "quantify",
    "report_progress",
    "SetFilter",
    "SizeFilter",
    "StringFilter",
    "TempDir",
    "TempEnv",
    "TempFile",
    "Template",
    "TimeFilter",
    "Timer",
    "ZoneInfo",
]

from .datetime import ZoneInfo, format_datetime, get_datetime, get_tzinfo
from .dicts import AttrDict, attrify, flatten_dotdict, get_field, inflate_dotdict
from .files import AnyFile, AnyPath, BinFile, TempDir, TempFile, fileglob, open_any
from .filters import (
    AutoFilter,
    BaseFilter,
    BoolFilter,
    ExpressionFilter,
    Filters,
    IncludeExcludeFilter,
    NullFilter,
    NumberFilter,
    SetFilter,
    SizeFilter,
    StringFilter,
    TimeFilter,
)
from .formatters import (
    Template,
    Timer,
    format_query_string,
    format_template,
    format_url,
    hrsize,
    hrtime,
    pluralize,
    quantify,
    report_progress,
)
from .json import json_encoder
from .parsers import (
    Pattern,
    parse_field_name,
    parse_hrsize,
    parse_hrtime,
    parse_pattern,
    parse_url,
)
from .state import Cached, TempEnv
from .testing import assert_like

# patch / extend the built-in python json encoder
setattr(JSONEncoder, "orig_default", JSONEncoder.default)
setattr(JSONEncoder, "default", json_encoder)
