from typing import TypeVar, Sequence, Mapping, Any
from abc import ABC, abstractmethod

from runtime.serialization.core.member import Member

T = TypeVar('T')

class TypeActivator(ABC):
    """The type activator is responsible for creating instances of serializable types.
    """
    __slots__ = []

    def __init__(self, cls: type[T], members: Sequence[Member], strict: bool):
        pass

    @abstractmethod
    def create_instance(self, cls: type[T], data: Mapping[str, Any]) -> T:
        """Creates a new instance of the serializable (either in its base form,
        or a more derived type defined by the 'cls' parameter) and populates the
        members with the data defined by the 'data' parameter.

        Args:
            cls (type[T]): The type of which to create an instance.
            data (Mapping[str, Any]): _description_

        Returns:
            T: The object created.
        """
        pass