import builtins as bi
import operator
import sys
from typing import *

import setdoc
from datarepr import datarepr
from frozendict import frozendict
from unhash import unhash

__all__ = ["ArgsHolder"]


class _empty:
    pass


class ArgsHolder:

    __slots__ = ("_args", "_kwargs")

    args: tuple
    kwargs: frozendict

    @setdoc.basic
    def __add__(self: Self, other: Iterable) -> list:
        return list(self.args + tuple(other))

    @setdoc.basic
    def __bool__(self: Self) -> bool:
        return bool(len(self))

    @setdoc.basic
    def __contains__(self: Self, other: Any) -> bool:
        return other in self.args

    @setdoc.basic
    def __delitem__(self: Self, key: Any) -> None:
        data: list | dict
        k: int | slice | str
        k = self._key(key, allowsslice=True)
        if isinstance(k, str):
            data = dict(self)
            del data[k]
            self.kwargs = data
        else:
            data = list(self)
            del data[k]
            self.args = data

    @setdoc.basic
    def __eq__(self: Self, other: Any) -> bool:
        if type(self) is not type(other):
            return False
        return self._cmp() == other._cmp()

    @setdoc.basic
    def __ge__(self: Self, other: Any) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        return self._cmp() >= other._cmp()

    @setdoc.basic
    def __getitem__(self: Self, key: Any) -> Any:
        x: int | slice | str
        x = self._key(key, allowsslice=True)
        if isinstance(x, str):
            return self.kwargs[x]
        else:
            return tuple(self)[x]

    @setdoc.basic
    def __gt__(self: Self, other: Any) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        return self._cmp() > other._cmp()

    __hash__ = unhash

    @setdoc.basic
    def __init__(self: Self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs

    @setdoc.basic
    def __iter__(self: Self) -> Iterable:
        return iter(self.args)

    @setdoc.basic
    def __le__(self: Self, other: Any) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        return self._cmp() <= other._cmp()

    @setdoc.basic
    def __len__(self: Self) -> int:
        return len(self.args) + len(self.kwargs)

    @setdoc.basic
    def __lt__(self: Self, other: Any) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        return self._cmp() < other._cmp()

    @setdoc.basic
    def __mul__(self: Self, other: SupportsIndex) -> list:
        return list(self.args * other)

    @setdoc.basic
    def __ne__(self: Self, other: Any) -> bool:
        return not (self == other)

    @setdoc.basic
    def __or__(self: Self, other: Any) -> dict:
        return dict(self.kwargs | other)

    @setdoc.basic
    def __repr__(self: Self) -> str:
        return datarepr(type(self).__name__, *self, **self)

    @setdoc.basic
    def __reversed__(self: Self) -> reversed:
        return reversed(self.args)

    @setdoc.basic
    def __rmul__(self: Self, other: Any) -> list:
        return list(other * self.args)

    @setdoc.basic
    def __ror__(self: Self, other: Any) -> dict:
        return dict(other | self.kwargs)

    @setdoc.basic
    def __setitem__(self: Self, key: Any, value: Any) -> None:
        data: list | dict
        k: int | slice | str
        k = self._key(key, allowsslice=True)
        if isinstance(k, str):
            data = dict(self)
            data[k] = value
            self.kwargs = data
        else:
            data = list(self)
            data[k] = value
            self.args = data

    @setdoc.basic
    def __str__(self: Self) -> str:
        return repr(self)

    def _cmp(self: Self) -> tuple[tuple, frozendict]:
        return self.args, self.kwargs

    @classmethod
    def _key(cls: type, key: Any, *, allowsslice: bool) -> int | slice | str:
        if allowsslice and type(key) is slice:
            return key
        try:
            return operator.index(key)
        except Exception:
            return str(key)

    def apply(self: Self, callback: Callable) -> Any:
        return callback(*self, **self)

    def append(self: Self, item: Any, /) -> None:
        "This method appends the positional arguments by value."
        self.args += (item,)

    @property
    def args(self: Self) -> tuple:
        "This property represents the positional arguments."
        return self._args

    @args.setter
    def args(self: Self, value: Iterable) -> None:
        self._args = tuple(value)

    def clear(self: Self) -> None:
        "This method removes all positional and keyword arguments."
        self.args = ()
        self.kwargs = frozendict()

    @setdoc.basic
    def copy(self: Self) -> Self:
        return type(self)(*self, **self)

    def count(self: Self, value: Any, /) -> int:
        "This method counts how often value occures within the positional arguments."
        return self.args.count(value)

    def extend(self: Self, iterable: Iterable, /) -> None:
        "This method extends the positional arguments by the given iterable."
        self.args += tuple(iterable)

    def get(self: Self, key: Any, /, default: Any = None) -> Any:
        "This method returns the value of the specified keyword argument if it exists, otherwise default."
        return self.kwargs.get(str(key), default)

    def index(
        self: Self,
        value: Any,
        start: SupportsIndex = 0,
        stop: SupportsIndex = sys.maxsize,
    ) -> int:
        "This method returns the index of the first occurence of value within the positional arguments."
        return self.args.index(value, start, stop)

    def insert(self: Self, index: SupportsIndex, value: Any) -> None:
        "This method inserts value at index into the positional arguments."
        data: list
        data = list(self)
        data.insert(index, value)
        self.args = data

    def items(self: Self) -> Iterable:
        "This method returns the keyword arguments as tuples of key and value."
        return self.kwargs.items()

    def keys(self: Self) -> Iterable:
        "This method returns the keys of the keyword arguments."
        return self.kwargs.keys()

    @property
    def kwargs(self: Self) -> frozendict:
        "This property represents the keyword arguments."
        return self._kwargs

    @kwargs.setter
    def kwargs(self: Self, value: Any) -> None:
        self._kwargs = frozendict((str(x), y) for x, y in dict(value).items())

    def map(
        self: Self,
        callback: Callable,
        *,
        strict: Any,
    ) -> Generator[Any, None, None]:
        holder: Self
        for holder in self.zip(strict=strict):
            yield holder.apply(callback)

    @overload
    def pop(self: Self, key: SupportsIndex = -1, /) -> Any: ...

    @overload
    def pop(self: Self, key: Any, /) -> Any: ...

    @overload
    def pop(self: Self, key: Any, default: Any, /) -> Any: ...

    def pop(self: Self, key: Any = -1, default: Any = _empty, /) -> Any:
        ans: Any
        args: tuple
        data: list | dict
        x: int | str
        x = self._key(key, allowsslice=False)
        if default is _empty:
            args = (x,)
        else:
            args = x, default
        if isinstance(x, int):
            data = list(self)
        else:
            data = dict(self)
        ans = data.pop(*args)
        if isinstance(x, int):
            self.args = data
        else:
            self.kwargs = data
        return ans

    def popitem(self: Self) -> tuple[str, Any]:
        "This method pops the last keyword argument and returns it as tuple of key and value."
        ans: tuple
        data: dict
        data = dict(self)
        ans = data.popitem()
        self.kwargs = data
        return ans

    def remove(self: Self, value: Any, /) -> None:
        "This method removes the first occurence of value for the positional arguments."
        data: list
        data = list(self)
        data.remove(value)
        self.args = data

    def reverse(self: Self) -> None:
        "This method reverses the positional arguments."
        self.args = reversed(self)

    def setdefault(self: Self, key: Any, default: Any = None, /) -> Any:
        "This method returns the value of the indicated keyword argument after setting it to default if previously absent."
        ans: Any
        data: dict
        data = dict(self)
        ans = data.setdefault(str(key), default)
        self.kwargs = data
        return ans

    def sort(self: Self, *, key: Any = None, reverse: Any = False) -> Any:
        "This method sorts the positional arguments."
        self.args = sorted(self.args, key=key, reverse=bool(reverse))

    def update(self: Self, dictionary: Any = (), /, **kwargs: Any) -> None:
        "This method updates the keyword arguments."
        data: dict
        data = dict(self)
        data.update(dictionary, **kwargs)
        self.kwargs = data

    def values(self: Self) -> Iterable:
        "This method returns the values of the keyword arguments."
        return self.kwargs.values()

    def zip(self: Self, strict: Any = False) -> Generator[Self, None, None]:
        keys: tuple
        strict_: bool
        yargs: tuple
        ykwargs: dict
        yvalues: tuple
        zargs: bi.zip
        zdata: bi.zip
        zvalues: bi.zip
        keys = tuple(self.keys())
        strict_ = bool(strict)
        zargs = bi.zip(*self, strict=strict_)
        zvalues = bi.zip(*self.values(), strict=strict_)
        zdata = bi.zip(zargs, zvalues, strict=strict_)
        for yargs, yvalues in zdata:
            ykwargs = dict(bi.zip(keys, yvalues))
            yield type(self)(*yargs, **ykwargs)
