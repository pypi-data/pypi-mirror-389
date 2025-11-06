from __future__ import annotations
from typing import Any
from abc import ABC, abstractmethod
from typingutils import AnyType

from runtime.serialization.core.threading import Lock
from runtime.serialization.core.helpers import Result
from runtime.serialization.core.primitives import Primitives

class Formatter(ABC):
    """The formatter is responsible for encoding and decoding values to and from primitive types.
    """
    __formatter_cache_lock__ = Lock()
    __formatter_cache__: dict[type[Any], Formatter] = {}

    def __new__(cls, *args: Any, **kwargs: Any):
        with Formatter.__formatter_cache_lock__:
            if cls not in Formatter.__formatter_cache__:
                instance = object.__new__(cls)
                Formatter.__formatter_cache__[cls] = instance
                return instance
            else:
                return Formatter.__formatter_cache__[cls]

    @abstractmethod
    def encode(self, value: Any, member_type: AnyType | None) -> Result[Primitives]:
        """Encodes a value to a primitive form (booleans, integers, floats, strings, lists and dicts).

        Args:
            value (Any): The value to be encoded.
            member_type (AnyType | None): The member type specified by the model.

        Returns:
            Result[Primitives]: Returns a primitive value result.
        """
        ...

    @abstractmethod
    def decode(self, value: Primitives, member_type: AnyType | None) -> Result[Any]:
        """Decodes a value from a primitive form (booleans, integers, floats, strings, lists and dicts).

        Args:
            value (Primitives): The value to be decoded.
            member_type (AnyType | None): The member type specified by the model.

        Returns:
            Result[Any]: Returns a value result.
        """
        ...
