from abc import ABC, abstractmethod
from typing import Any, Sequence

from runtime.serialization.core.member import Member
from runtime.serialization.core.interfaces.type_activator import TypeActivator
from runtime.serialization.core.interfaces.injector import Injector


class SerializerAttributes(ABC):
    """The serializer attributes specifies certain attributes for a serializable type.
    """

    @property
    @abstractmethod
    def serializable(self) -> type[Any]:
        """The type which this class represents.
        """
        ...

    @property
    @abstractmethod
    def namespace(self) -> str | None:
        """The namespace of the serializeble.
        """
        ...

    @property
    @abstractmethod
    def type_name(self) -> str:
        """The name of the serializable.
        """
        ...

    @property
    @abstractmethod
    def strict(self) -> bool:
        """Indicates whether or not strict mode is applied.
        """
        ...

    @property
    @abstractmethod
    def type_activator(self) -> TypeActivator:
        """The type activator used to create instances of the serializable.
        """
        ...

    @property
    @abstractmethod
    def is_resolvable(self) -> bool:
        """Indicates whether or not the serialziable can be resolved
        to a more derived type by a special type resolver.
        """
        ...

    @property
    @abstractmethod
    def injector(self) -> Injector | None:
        """The optional injector used to inject values onto NULL members.
        """
        ...

    @property
    @abstractmethod
    def members(self) -> Sequence[Member]:
        """The serializables members.
        """
        ...