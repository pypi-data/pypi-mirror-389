"""Filter expression parsing and evaluation."""

import abc
import operator
import re
import typing as t
from datetime import datetime
from functools import partial

from .datetime import get_datetime
from .dicts import get_field
from .parsers import parse_and_strip_regex_opts, parse_hrsize, simple_regex

__all__ = [
    "AutoFilter",
    "BaseFilter",
    "BoolFilter",
    "ExpressionFilter",
    "Filters",
    "IncludeExcludeFilter",
    "NullFilter",
    "NumberFilter",
    "SetFilter",
    "SizeFilter",
    "StringFilter",
    "TimeFilter",
]


def eq_tilde(value: str, pattern: t.Pattern) -> bool:
    """Return True if the regex pattern matches the value."""
    return bool(pattern.search(value))


def ne_tilde(value: str, pattern: t.Pattern) -> bool:
    """Return True if the regex pattern does not match the value."""
    return not eq_tilde(value, pattern)


TYPES = type(None), bool, int, float, datetime, str, list, tuple, set
OPERATORS: t.Dict[str, t.Callable] = {
    "=": operator.eq,
    "!=": operator.ne,
    "<": operator.lt,
    ">": operator.gt,
    "<=": operator.le,
    ">=": operator.ge,
    "=~": eq_tilde,
    "!~": ne_tilde,
}

BASIC_OPS = ["=", "!="]
COMMON_OPS = ["=", "!=", "<", ">", "<=", ">="]
STRING_OPS = ["=", "!=", "<", ">", "<=", ">=", "=~", "!~"]


Filters = t.List[str]


class BaseFilter(abc.ABC):
    """Base filter class defining the filter interface."""

    @abc.abstractmethod
    def match(self, value) -> bool:
        """Return True if the filter matches value."""


class ExpressionFilter(BaseFilter):
    """Expression filter tied to a field, operator and value."""

    operators: t.ClassVar[t.List[str]] = COMMON_OPS

    def __init__(self, field: str, op: str, value: str) -> None:
        """Initialize an expression filter."""
        if op not in self.operators:
            expected = "|".join(self.operators)
            raise ValueError(f"invalid operator: {op} (expected {expected})")
        if "~" in op:
            try:  # validate regexes early
                pattern, opts = parse_and_strip_regex_opts(value)
                pattern = pattern if "r" in opts else simple_regex(pattern, False)
                self.parsed = re.compile(pattern, flags=re.I)
            except re.error as exc:
                raise ValueError(f"invalid regex: {value} - {exc}") from exc
        else:
            self.parsed = value.lower()
        self.field = field
        self.op = op
        self.value = value

    def __str__(self) -> str:
        """Return human-readable stringification (the original expression)."""
        return f"{self.field}{self.op}{self.value}"

    def __repr__(self) -> str:
        """Return the filter's string representation."""
        cls_args = self.field, self.op, self.value
        return f"{type(self).__name__}{cls_args!r}"

    def get_match_field(self, value):
        """Return the value for simple types and the field attr/key for dict/obj."""
        return value if isinstance(value, TYPES) else get_field(value, self.field)

    def compare(self, value) -> bool:
        """Return the operator's output comparing the given val to the filter val."""
        return OPERATORS[self.op](value, self.parsed)


class IncludeExcludeFilter(BaseFilter):
    """Filter supporting multiple include- and exclude expressions."""

    def __init__(
        self,
        factory: t.Dict[str, t.Type[ExpressionFilter]],
        *,
        include: Filters = None,
        exclude: Filters = None,
        validate: t.Callable[[str], str] = None,
    ) -> None:
        """Init a complex filter from multiple include- and exclude expressions.

        Args:
            factory: Field name to filter class mapping used as a factory.
            include: List of include exprs - if given, at least one must match.
            exclude: List of exclude exprs - if given, none are allowed to match.
            validate: Field name validator callback.
        """
        parse = partial(parse_filter_expression, factory=factory, validate=validate)
        self.include = [parse(expr) for expr in (include or [])]
        self.exclude = [parse(expr) for expr in (exclude or [])]

    def match(self, value, exclude_only: t.List[str] = None) -> bool:
        """Return whether value matches all includes but none of the excludes.

        If `exclude_only` is given, only evaluate the exclude filters on those.
        """
        include = self.include
        exclude = self.exclude
        if exclude_only:
            include = []
            exclude = [filt for filt in exclude if filt.field in exclude_only]
        include_match = (i.match(value) for i in include)
        exclude_match = (e.match(value) for e in exclude)
        return (not include or any(include_match)) and not any(exclude_match)

    def __repr__(self) -> str:
        """Return string representation of the filter object."""
        cls_name = self.__class__.__name__
        include = ",".join(f"'{filt}'" for filt in self.include)
        exclude = ",".join(f"'{filt}'" for filt in self.exclude)
        return f"{cls_name}(include=[{include}], exclude=[{exclude}])"


class AutoFilter(ExpressionFilter):
    """Filter with dynamic type detection based on the value being matched."""

    operators = OPERATORS

    def __init__(self, field: str, op: str, value: str) -> None:
        """Initialize automatic/dynamic filter."""
        super().__init__(field, op, value)

    def match(self, value) -> bool:
        """Compare value to the filter value based on type."""
        value = self.get_match_field(value)
        filter_args = self.field, self.op, self.value
        if isinstance(value, (list, tuple, set)):
            return SetFilter(*filter_args).match(value)
        try:
            if value is None:
                return NullFilter(*filter_args).match(value)
            if isinstance(value, bool):
                return BoolFilter(*filter_args).match(value)
            if isinstance(value, (int, float)):
                return NumberFilter(*filter_args).match(value)
        except ValueError:
            if value is None:
                return False
            value = str(value)
        # TODO consider adding support for size/time
        return StringFilter(*filter_args).match(value)


class NullFilter(ExpressionFilter):
    """Null filter."""

    operators = BASIC_OPS

    def __init__(self, field: str, op: str, value: str) -> None:
        """Initialize null filter from str value."""
        super().__init__(field, op, value)
        null_re = r"null|none|nil"
        if not re.match(null_re, value, flags=re.I):
            raise ValueError(f"invalid null: {value!r} (expected: {null_re})")
        self.parsed = None

    def match(self, value) -> bool:
        """Check whether the given value is/isn't None."""
        value = self.get_match_field(value)
        return self.compare(value)


class BoolFilter(ExpressionFilter):
    """Bool filter."""

    operators = BASIC_OPS

    def __init__(self, field: str, op: str, value: str) -> None:
        """Initialize bool filter from str value."""
        super().__init__(field, op, value)
        true_re = r"true|1"
        false_re = r"false|0"
        if re.match(true_re, value, flags=re.I):
            self.parsed = True
        elif re.match(false_re, value, flags=re.I):
            self.parsed = False
        else:
            expected = f"(expected: {'|'.join([true_re, false_re])})"
            raise ValueError(f"invalid boolean: {value!r} {expected}")

    def match(self, value) -> bool:
        """Compare a boolean to the filter value."""
        value = self.get_match_field(value)
        return self.compare(value)


class NumberFilter(ExpressionFilter):
    """Number filter."""

    operators = COMMON_OPS

    def __init__(self, field: str, op: str, value: str) -> None:
        """Initialize number filter from str value."""
        super().__init__(field, op, value)
        self.parsed = float(value)

    def match(self, value) -> bool:
        """Compare number to the filter value."""
        value = self.get_match_field(value)
        # guard against comparing incompatible types w/ lt/gt/etc.
        if not isinstance(value, (int, float)):
            return False
        return self.compare(value)


class SetFilter(ExpressionFilter):
    """Set filter."""

    operators = ["=", "!=", "=~", "!~"]  # ie. in / not in
    pattern: t.Union[str, t.Pattern]

    def __init__(self, field: str, op: str, value: str) -> None:
        """Initialize set filter from str value."""
        super().__init__(field, op, value.lower())

    def match(self, value) -> bool:
        """Return that the given item is in the given list/tuple/set."""
        value = self.get_match_field(value)
        # treat nulls as empty lists
        if value is None:
            value = []
        # guard against iterating incompatible types
        if not isinstance(value, (list, tuple, set)):
            return False
        # coerce list elements to strings to allow regex matching
        vals = [str(val).lower() for val in value]
        func = all if self.op.startswith("!") else any
        return func(self.compare(val) for val in vals)


class StringFilter(ExpressionFilter):
    """String filter."""

    operators = STRING_OPS
    string: t.Union[str, t.Pattern]

    def match(self, value) -> bool:
        """Match str with the filter's regex pattern."""
        value = self.get_match_field(value)
        # return false regardless of operator when comparing to null
        if value is None:
            return False
        # coerce values to strings to allow regex matching
        return self.compare(str(value).lower())


class SizeFilter(ExpressionFilter):
    """Size filter."""

    operators = COMMON_OPS

    def __init__(self, field: str, op: str, value: str) -> None:
        """Initialize size filter from a human-readable size."""
        super().__init__(field, op, value)
        self.parsed = parse_hrsize(value)

    def match(self, value: t.Union[int, t.Any]) -> bool:
        """Compare size to the filter value."""
        value = self.get_match_field(value)
        # return false regardless of operator when comparing to null
        if value is None:
            return False
        return self.compare(value)


class TimeFilter(ExpressionFilter):
    """Time filter."""

    operators = COMMON_OPS
    timestamp_re = re.compile(
        r"(?i)"
        r"(?P<year>\d\d\d\d)([-_/]?"
        r"(?P<month>\d\d)([-_/]?"
        r"(?P<day>\d\d)([-_/T ]?"
        r"(?P<hour>\d\d)([-_:]?"
        r"(?P<minute>\d\d)([-_:]?"
        r"(?P<second>\d\d)?)?)?)?)?)?"
    )

    def __init__(self, field: str, op: str, value: str) -> None:
        """Initialize time filter from an iso-format timestamp."""
        super().__init__(field, op, value)
        if not (match := self.timestamp_re.match(value)):
            raise ValueError(f"invalid time: {value!r} (expected YYYY-MM-DD HH:MM:SS)")
        if match.group("second"):
            self.parsed = get_datetime(value).strftime("%Y%m%d%H%M%S")
        else:
            self.parsed = "".join(part or "" for part in match.groupdict().values())

    def match(self, value: t.Union[int, str, datetime, t.Any]) -> bool:
        """Compare timestamp to the filter value."""
        value = self.get_match_field(value)
        # return false regardless of operator when comparing to other types
        if not isinstance(value, (int, str, datetime)):
            return False
        value = get_datetime(value).strftime("%Y%m%d%H%M%S")[: len(self.parsed)]
        return self.compare(value)


def parse_filter_expression(
    expression: str,
    factory: t.Dict[str, t.Type[ExpressionFilter]],
    validate: t.Callable[[str], str] = None,
) -> ExpressionFilter:
    """Parse and return filter from expression string (factory)."""
    op_re = "|".join(sorted(OPERATORS, key=len, reverse=True))
    expr_split = re.split(rf"(?<=\w)({op_re})", expression, maxsplit=1)
    if len(expr_split) != 3:
        raise ValueError(f"invalid filter expression: {expression}")
    field, op, value = expr_split
    # NOTE compat for == in lieu of =
    if op == "=" and value.startswith("="):
        value = value[1:]
    # TODO consider to enable shorthands based on factories if no validator passed
    field = validate(field) if validate else field
    filter_cls: t.Optional[t.Type[ExpressionFilter]] = None
    for k, filter_cls in factory.items():
        if field == k or k.endswith("*") and field.startswith(k[:-1]):
            break
    return (filter_cls or StringFilter)(field, op, value)
