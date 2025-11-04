import ctypes
from typing import (
    KT,
    VT,
    Any,
    Callable,
    Iterable,
    Iterator,
    MutableMapping,
    MutableSequence,
    Optional,
    Sequence,
    T,
    T_co,
    Union,
    VT_co,
)

from deepdiff import DeepHash

# The following immutable objects can't reference other objects so are directly observed
_DIRECTLY_OBSERVABLE_INTRISTICS = (bool, int, str, float, bytes)
_DIRECTLY_OBSERVABLE = (*_DIRECTLY_OBSERVABLE_INTRISTICS, ctypes._SimpleCData)


def _run_deephash(obj: Any) -> int:
    return int(
        DeepHash(obj, exclude_types=[ctypes.Structure, ctypes.Union, ctypes._SimpleCData])[obj], 16
    )


class ObservableBase:
    def __init__(self, __v: T, observer: Optional[Callable[[Any], Any]] = None, **kwargs) -> None:
        super().__init__()
        self.__data = __v
        self.__hash = self.__hash__()
        self.__observer = observer
        self.__modified = False

    def __hash__(self) -> int:
        if isinstance(self.__data, _DIRECTLY_OBSERVABLE_INTRISTICS):
            return hash(self.__data)
        elif isinstance(self.__data, (ctypes.Structure, ctypes.Union, ctypes._SimpleCData)):
            return hash(bytes(self.__data))
        else:
            return _run_deephash(self.__data)

    def __clear_modified_flags(self) -> None:
        if isinstance(self.__data, MutableMapping):
            for item in self.__data.values():
                item.modified = False
        elif isinstance(self.__data, MutableSequence):
            for item in self.__data:
                item.modified = False
        self.__modified = False

    @property
    def modified(self) -> bool:
        if self.__modified:
            return True
        elif not isinstance(self.__data, (*_DIRECTLY_OBSERVABLE, ObservableBase)):
            self.__modified = self.__hash != self.__hash__()
        return self.__modified

    @modified.setter
    def modified(self, value) -> None:
        if value:
            self.__modified = True
        elif self.__modified:
            self.__clear_modified_flags()
            self.__hash = self.__hash__()

    @property
    def value(self) -> T:
        return self.__data

    @value.setter
    def value(self, value: T) -> None:
        self.notify(True)
        self.__data = value if isinstance(value, type(self.__data)) else type(self.__data)(value)

    def make_observable(self, value: T) -> Any:
        return Observable(value, self.__observer)

    def notify(self, value):
        self.__modified = value
        if self.__observer:
            self.__observer(value)

    def __getattr__(self, __name: str) -> Any:
        if __name.startswith(("_ObservableBase", "__")):
            return super().__getattribute__(__name)
        else:
            return getattr(self.__data, __name)

    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name.startswith(("_ObservableBase", "__", "value", "modified")):
            super().__setattr__(__name, __value)
        else:
            self.notify(True)
            setattr(self.__data, __name, __value)

    def __eq__(self, __value: object) -> bool:
        return self.__data == __value

    def __ne__(self, __value: object) -> bool:
        return self.__data != __value

    def __lt__(self, __value: object) -> bool:
        return self.__data < __value

    def __lte__(self, __value: object) -> bool:
        return self.__data <= __value

    def __gt__(self, __value: object) -> bool:
        return self.__data > __value

    def __gte__(self, __value: object) -> bool:
        return self.__data >= __value


class ObservableList(ObservableBase, MutableSequence[T]):
    def __init__(self, __v: Sequence[T], observer: Callable[[Any], Any]) -> None:
        super().__init__([Observable(item) for item in __v], observer=observer)

    def __setitem__(self, __is: Union[int, slice], __vo: Union[str, Iterable[str]]) -> None:
        self.notify(True)
        if isinstance(__is, slice) and isinstance(__vo, Iterable):
            self.value.__setitem__(__is, [self.make_observable(x) for x in __vo])
        else:
            self.value.__setitem__(__is, self.make_observable(__vo))

    def __getitem__(self, __is: Union[int, slice]) -> T:
        item = self.value[__is]
        if isinstance(__is, slice):
            return self.make_observable(item)
        else:
            return item.value if isinstance(item.value, _DIRECTLY_OBSERVABLE) else item

    def __delitem__(self, __i) -> None:
        self.notify(True)
        del self.value[__i]

    def __len__(self) -> int:
        return len(self.value)

    def insert(self, __i: int, __v: T) -> None:
        self.notify(True)
        return self.value.insert(__i, __v)


class ObservableDict(ObservableBase, MutableMapping[KT, VT]):
    def __init__(self, *args, observer: Callable[[Any], Any], **kwargs: Any) -> None:
        __v = {k: Observable(v, observer) for k, v in dict(*args, **kwargs).items()}
        super().__init__(__v, observer=observer)

    def __getitem__(self, __k: KT) -> VT_co:
        item = self.value[__k]
        return item.value if isinstance(item.value, _DIRECTLY_OBSERVABLE) else item

    def __delitem__(self, __k: KT) -> None:
        self.notify(True)
        self.value.__delitem__(__k)

    def __setitem__(self, __k: KT, __v: VT) -> None:
        self.notify(True)
        self.value[__k] = self.make_observable(__v)

    def __iter__(self) -> Iterator[T_co]:
        return iter(self.value)

    def __len__(self) -> int:
        return len(self.value)


def Observable(target: T, callback=None) -> Union[ObservableBase, ObservableList, ObservableDict]:
    if isinstance(target, MutableMapping):
        return ObservableDict(target, observer=callback)
    elif isinstance(target, MutableSequence):
        return ObservableList(target, observer=callback)
    return ObservableBase(target, observer=callback)


class State:
    def __init__(self, **kwargs) -> None:
        self.__data = ObservableDict(observer=None, **kwargs)

    def __getattr__(self, __name: str) -> Any:
        if __name.startswith(("_State", "__")):
            return super().__getattribute__(__name)
        else:
            return self.__data[__name]

    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name.startswith(("_State", "__", "modified")):
            super().__setattr__(__name, __value)
        else:
            self.__data[__name] = __value

    def __hash__(self) -> int:
        return hash(self.__data)

    def add_variable(self, name: str, value: Any) -> None:
        self.__data[name] = value

    @property
    def modified(self):
        return self.__data.modified

    @modified.setter
    def modified(self, value):
        self.__data.modified = value

    @property
    def context(self):
        return self.__data


__all__ = ["State", "Observable"]
