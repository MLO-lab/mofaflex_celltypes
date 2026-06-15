from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import Enum, auto
from functools import partial
from itertools import chain
from types import MethodType
from typing import TYPE_CHECKING, Generic, Self, TypeVar

if TYPE_CHECKING:
    from .mofaflex import MOFAFLEX


class _class_and_instancemethod:
    def __init__(self, func):
        self._func = func
        self._clsfunc = classmethod(func)

    def __get__(self, instance, owner):
        obj = self._func if instance is not None else self._clsfunc
        return obj.__get__(instance, owner)


class APIType(Enum):
    method = auto()
    property = auto()


@dataclass(kw_only=True, frozen=True)
class DynamicAPI:
    """Description of a user-facing API attribute."""

    name: str
    """The name of the attribute."""

    type: APIType
    """The type of the attribute (method or property)."""

    hidden: bool = False
    """Whether the attribute is hidden. Hidden attributes are not listed by `dir()`, but can still be accessed."""

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other: str | DynamicAPI):
        if isinstance(other, __class__):
            other = other.name
        return self.name == other


class DynamicAPIDecorator:
    @staticmethod
    def add_api(owner, api: str, type, **kwargs):
        if "__dynamicapi_apiset__" not in owner.__dict__:
            owner.__dynamicapi_apiset__ = owner.__dynamicapi_apiset__.copy()
        api = owner.__dynamicapi_apicls__(name=api, type=type, **kwargs)
        owner.__dynamicapi_apiset__.discard(api)
        owner.__dynamicapi_apiset__.add(api)

    def __init__(self, func: Callable | property, **kwargs):
        self._func = func
        self._kwargs = kwargs
        if isinstance(func, property):
            self.setter = self._setter
            self.deleter = self._deleter

    def __set_name__(self, owner, name: str):
        self.add_api(
            owner, name, APIType.property if isinstance(self._func, property) else APIType.method, **self._kwargs
        )
        setattr(owner, name, self._func)

    def _setter(self, func):
        self._func = self._func.setter(func)
        return self

    def _deleter(self, func):
        self._func = self._func.deleter(func)
        return self


class DynamicAPIMixin:
    """Mixin class for classes that define a subset of their API as user-facing.

    The non-userfacing API is intented to be used internally in MOFA-FLEX, while the user-facing
    API is exposed to the end user through e.g. a wrapper class. API methods and properties can
    be defined both at the class level as well as for individual instances.
    """

    __dynamicapi_apiset__ = set()
    __dynamicapi_apicls__ = DynamicAPI
    __dynamicapi_decorator_cls__ = DynamicAPIDecorator

    def __init_subclass__(
        subcls,
        *,
        dynapi_cls: type[DynamicAPI] | None = None,
        dynapi_decorator_cls: type[DynamicAPIDecorator] | None = None,
        **kwargs,
    ):
        super().__init_subclass__(**kwargs)
        if dynapi_cls is not None:
            subcls.__dynamicapi_apicls__ = dynapi_cls
        if dynapi_decorator_cls is not None:
            subcls.__dynamicapi_decorator_cls__ = dynapi_decorator_cls

    @_class_and_instancemethod
    def api(self) -> Iterable[str]:
        """The user-facing API of class / object."""
        return self.__dynamicapi_apiset__

    @_class_and_instancemethod
    def api_methods(self) -> Iterable[DynamicAPI]:
        """The user-facing methods of this class / object."""
        return (api for api in self.__dynamicapi_apiset__ if api.type == APIType.method)

    @_class_and_instancemethod
    def api_properties(self) -> Iterable[DynamicAPI]:
        """The user-facing properties of this class / object."""
        return (api for api in self.__dynamicapi_apiset__ if api.type == APIType.property)

    @_class_and_instancemethod
    def _api(self: type[Self], obj: Callable | MethodType | property | str | None = None, **kwargs):
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
        if isinstance(self, type) and issubclass(self, __class__) and obj is None:
            return partial(self._api, **kwargs)
        elif isinstance(self, type) and issubclass(self, __class__) and isinstance(obj, Callable | property):
            return self.__dynamicapi_decorator_cls__(obj, **kwargs)
        elif isinstance(self, __class__) and isinstance(obj, MethodType):
            self.__dynamicapi_decorator_cls__.add_api(obj.__self__, obj.__name__, APIType.method, **kwargs)
            return None
        elif isinstance(obj, str):
            cls = self.__class__ if isinstance(self, __class__) else self
            type_ = APIType.method
            try:
                if isinstance(getattr(cls, obj), property):
                    type_ = APIType.property
            except AttributeError:
                if not isinstance(getattr(self, obj), MethodType):
                    type_ = APIType.property
            self.__dynamicapi_decorator_cls__.add_api(self, obj, type_, **kwargs)
            return None
        else:
            raise TypeError("Unknown argument type for 'obj'")


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
