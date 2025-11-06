from __future__ import annotations
from typing import Any, IO, TypeVar, Generic, cast, overload
from io import TextIOBase
from abc import ABC, abstractmethod
from typingutils import AnyType, get_generic_arguments

from runtime.serialization.core.threading import Lock

T = TypeVar("T")

class Serializer(Generic[T], ABC):
    __serializer_cache_lock__ = Lock()
    __serializer_cache__: dict[tuple[type[Any], AnyType], Serializer[Any]] = {}
    __serializable: type[Any]

    def __new__(cls, *args: Any, **kwargs: Any):
        serializable, *_ = get_generic_arguments(cls)
        key = (cls, serializable)
        with Serializer.__serializer_cache_lock__:
            if key not in Serializer.__serializer_cache__:
                instance = object.__new__(cls)
                instance.__serializable = cast(type[Any], serializable)
                Serializer.__serializer_cache__[key] = instance
                return instance
            else:
                return Serializer.__serializer_cache__[key]

    @property
    def serializable(self) -> type[Any]:
        """The type which this class is able to serialize and deserialize.
        """
        return self.__serializable


    @overload
    @abstractmethod
    def serialize(self, obj: T) -> str:
        """Serializes object as a string.

        Args:
            obj (T): The object to serialize.

        Returns:
            str: Returns a string serialization.
        """
        ...
    @overload
    @abstractmethod
    def serialize(self, obj: T, base: type[T]) -> str:
        """Serializes object as a string using a more derived base type than T.

        Args:
            obj (T): The object to serialize.
            base (type[T]): The base type.

        Returns:
            str: Returns a string serialization.
        """
        ...

    @abstractmethod
    def deserialize(self, text: str) -> T:
        """Deserializes object from a string.

        Args:
            text (str): The serialization string.

        Returns:
            T: Returns an object.
        """
        ...

    @overload
    @abstractmethod
    def load(self, input: TextIOBase | IO[Any]) -> T:
        """Deserializes object from a file or IO input.

        Args:
            input (TextIOBase | IO[Any]): The input.

        Returns:
            T: Returns an object.
        """
        ...
    @overload
    @abstractmethod
    def load(self, input: str) -> T:
        """Deserializes object from a file.

        Args:
            input (str): The path of the file.

        Returns:
            T: Returns an object.
        """
        ...

    @abstractmethod
    def loads(self, text: str) -> T:
        """Deserializes object from a string.

        Args:
            text (str): The string to deserialize.

        Returns:
            T: Returns an object.
        """
        ...

    @overload
    @abstractmethod
    def dump(self, obj: T, output: TextIOBase | IO[Any], **kwargs: Any) -> None:
        """Serializes object to a file or IO output.

        Args:
            obj (T): The object to serialize.
            output (TextIOBase | IO[Any]): The output.
        """
        ...
    @overload
    @abstractmethod
    def dump(self, obj: T, output: str, *, overwrite: bool = False, **kwargs: Any) -> None:
        """Serializes object to a file.

        Args:
            obj (T): The object to serialize.
            output (str): The path of the output file.
            overwrite (bool): Specifies whether or not to overwrite file if it exists.
        """
        ...

    @abstractmethod
    def dumps(self, obj: T) -> str:
        """Serializes object to a string.

        Args:
            obj (T): The object to serialize.

        Returns:
            str: Returns a string.
        """
        ...