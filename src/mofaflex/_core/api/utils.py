from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from itertools import chain
from types import MethodType
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from .mofaflex import MOFAFLEX


class _class_and_instancemethod:
    def __init__(self, func):
        self._func = func
        self._clsfunc = classmethod(func)

    def __get__(self, instance, owner):
        obj = self._func if instance is not None else self._clsfunc
        return obj.__get__(instance, owner)


@dataclass(kw_only=True, frozen=True)
class DynamicAPI:
    name: str
    hidden: bool = False

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other: str | DynamicAPI):
        if isinstance(other, __class__):
            other = other.name
        return self.name == other


class DynamicAPIMixin:
    """Mixin class for classes that define a subset of their API as user-facing.

    The non-userfacing API is intented to be used internally in MOFA-FLEX, while the user-facing
    API is exposed to the end user through e.g. a wrapper class. API methods and properties can
    be defined both at the class level as well as for individual instances.
    """

    _apiset = set()

    @_class_and_instancemethod
    def api(self) -> Iterable[str]:
        """The user-facing API of class / object."""
        return self._apiset

    @_class_and_instancemethod
    def api_methods(self) -> Iterable[DynamicAPI]:
        """The user-facing methods of this class / object."""
        obj = self.__class__ if isinstance(self, __class__) else self
        return (api for api in self._apiset if not isinstance(getattr(obj, api.name, None), property))

    @_class_and_instancemethod
    def api_properties(self) -> Iterable[DynamicAPI]:
        """The user-facing properties of this class / object."""
        obj = self.__class__ if isinstance(self, __class__) else self
        return (api for api in self._apiset if isinstance(getattr(obj, api.name, None), property))

    def _api(
        obj: Callable | property | DynamicAPIMixin | type[DynamicAPIMixin] | None,
        attr: MethodType | property | str | None = None,
        *,
        hidden: bool = False,
    ):
        """Mark a method or property as user-facing.

        Subclasses can use this to expose properties or methods to the end user.

        This can be used both as a decorator and as a method.

        Examples:
            To use as a decorator:

            >>> @DynamicAPIMixin._api
            ... def foo(self, x, y):
            ...     pass

            When used with properties, it must be stacked above the property decorator:

            >>> @DynamicAPIMixin._api
            ... @property
            ... def bar(self):
            ...     pass

            To use as a method at runtime:

            >>> def baz(self, *args):
            ...     pass
            ...
            ...
            ... def foobar(self, *args):
            ...     self._api("baz")

            Alternatively:
            >>> def foobar(self, *args):
            ...     self._api(self.baz)
        """

        def _add_api(owner, api: str):
            if "_apiset" not in owner.__dict__:
                owner._apiset = owner._apiset.copy()
            api = DynamicAPI(name=api, hidden=hidden)
            owner._apiset.discard(api)
            owner._apiset.add(api)

        class __api:
            def __new__(cls, func: Callable | MethodType | property):
                if isinstance(func, MethodType):
                    _add_api(func.__self__, func.__name__)
                    return None
                else:
                    return super().__new__(cls)

            def __init__(self, func: Callable | property):
                self._hidden = hidden
                self._func = func
                if isinstance(func, property):
                    self.setter = self._setter
                    self.deleter = self._deleter

            def __set_name__(self, owner, name: str):
                _add_api(owner, name)
                setattr(owner, name, self._func)

            def _setter(self, func):
                self._func = self._func.setter(func)
                return self

            def _deleter(self, func):
                self._func = self._func.deleter(func)
                return self

        if obj is None:
            return __api
        elif isinstance(obj, Callable | property) and not isinstance(obj, __class__) and not isinstance(obj, type):
            return __api(obj)
        elif isinstance(attr, MethodType):
            return __api(attr)
        elif attr is None:
            raise ValueError("Need attr if invoked on a DynamicAPIMixin instance.")
        _add_api(obj, attr)
        return obj


T = TypeVar("T", bound=DynamicAPIMixin)


class DynamicAPIWrapper(Generic[T]):
    """Wrapper class for classes with a dynamic API hat only exposes the user-facing API.

    If a requested attribute is not found and `forward == True`, the wrapper tries to get it from the main
    MOFAFLEX instance. This is helpful to be able to access things like `n_samples` and `n_features`
    directly from terms without also having access to the MOFAFLEX instance.
    """

    def __init__(self, model: MOFAFLEX, wrapped: T, forward: bool = True):
        self._model = model
        self._wrapped = wrapped
        self._forward = forward

    def __dir__(self, forward: bool | None = None):
        apis = (api.name for api in self._wrapped.api() if not api.hidden)
        return chain(self._model.__dir__(), apis) if forward or forward is None and self._forward else apis

    def __getattr__(self, name, forward: bool | None = None):
        err = AttributeError(
            f"'{self._wrapped.__class__.__name__}' object has no attribute '{name}'", name=name, obj=self._wrapped
        )
        if name in self._wrapped.api():
            return getattr(self._wrapped, name)
        elif forward or forward is None and self._forward:
            try:
                return getattr(self._model, name)
            except AttributeError as e:
                raise err from e
        else:
            raise err
