from abc import ABC, abstractmethod
from typing import TypeVar

from runtime.serialization.core.member import Member
from runtime.serialization.core.helpers import Result

T = TypeVar("T")

class Injector(ABC):
    """The Injector class is intended for injecting values into objects when they are null.
    """

    @abstractmethod
    def try_inject_null_property(self, obj_type: type[T], member: Member) -> Result[T]:
        """If applicable, returns an object to be injected into the specific member of the object serialized.

        Args:
            obj_type (type[Any]): The serializable type.
            member (Member): The member onto which object is injected.

        Returns:
            Result[Any]: Returns a value result.
        """
        return None, False