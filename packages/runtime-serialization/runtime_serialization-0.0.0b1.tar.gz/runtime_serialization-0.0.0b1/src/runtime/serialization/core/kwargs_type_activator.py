from typing import TypeVar, Sequence, Mapping, Any
from runtime.reflection.lite import ParameterKind, get_constructor

from runtime.serialization.core.not_serializable_exception import NotSerializableException
from runtime.serialization.core.member import Member
from runtime.serialization.core.interfaces.type_activator import TypeActivator

T = TypeVar('T')

class KwargsTypeActivator(TypeActivator):
    """
    A type activator for classes having a constructor with only a kwargs parameter.
    """

    __slots__ = ["__strategy"]

    def __init__(self, cls: type, members: Sequence[Member], strict: bool):
        sig = get_constructor(cls)
        unwanted_parameters = [ p for p in sig.parameters if p.kind != ParameterKind.KWARGS ]
        kwargs = [ p for p in sig.parameters if p.kind == ParameterKind.KWARGS ]

        if not unwanted_parameters and kwargs:
            # class accepts **kwargs parameter
            pass
        else:
            raise NotSerializableException(cls, "KwargsTypeActivator cannot deserialize type")


    def create_instance(self, cls: type[T], data: Mapping[str, Any]) -> T:
        return cls(**data)
