from __future__ import annotations
from typing import TypeVar

from runtime.serialization.core.serializer_attributes import SERIALIZABLE_LOCK, SERIALIZABLES
from runtime.serialization.core.interfaces.type_activator import TypeActivator
from runtime.serialization.core.interfaces.injector import Injector
from runtime.serialization.core.decorators.decorator_exception import DecoratorException

T = TypeVar("T")

SERIALIZABLE_ATTRIBUTES: dict[type, SerializableAttributes] = {}

class SerializableAttributes:
    __slots__ = [ "__namespace", "__strict", "__type_activator", "__type_finder", "__injector" ]

    def __init__(
        self, *,
        namespace: str | None = None,
        strict: bool | None = None,
        type_activator: type[TypeActivator] | None = None,
        injector: type[Injector] | None = None
    ):
        self.__namespace = namespace
        self.__strict = strict
        self.__type_activator = type_activator
        self.__injector = injector

    @property
    def namespace(self) -> str | None:
        return self.__namespace

    @namespace.setter
    def namespace(self, value: str):
        if self.__namespace is not None:
            raise DecoratorException("Namespace attribute is already specified") # pragma: no cover
        self.__namespace = value

    @property
    def strict(self) -> bool | None:
        return self.__strict

    @strict.setter
    def strict(self, value: bool):
        if self.__strict is not None:
            raise DecoratorException("Strict attribute is already specified") # pragma: no cover
        self.__strict = value

    @property
    def type_activator(self) -> type[TypeActivator] | None:
        return self.__type_activator

    @type_activator.setter
    def type_activator(self, value: type[TypeActivator]):
        if self.__type_activator is not None:
            raise DecoratorException("Deserializer attribute is already specified") # pragma: no cover
        self.__type_activator = value

    @property
    def injector(self) -> type[Injector] | None:
        return self.__injector

    @injector.setter
    def injector(self, value: type[Injector]):
        if self.__injector is not None:
            raise DecoratorException("Injector attribute is already specified") # pragma: no cover
        self.__injector = value


def get_or_set_attributes(
    cls: type, *,
    namespace: str | None = None,
    strict: bool | None = None,
    type_activator: type[TypeActivator] | None = None,
    injector: type[Injector] | None = None
) -> SerializableAttributes:
    with SERIALIZABLE_LOCK:
        if cls not in SERIALIZABLES:
            if cls not in SERIALIZABLE_ATTRIBUTES:
                attributes = SerializableAttributes(
                    namespace = namespace,
                    strict = strict,
                    type_activator = type_activator,
                    injector = injector
                )
                SERIALIZABLE_ATTRIBUTES[cls] = attributes
            else:
                attributes = SERIALIZABLE_ATTRIBUTES[cls]
                if namespace is not None:
                    attributes.namespace = namespace
                if strict is not None:
                    attributes.strict = strict
                if type_activator is not None:
                    attributes.type_activator = type_activator
                if injector is not None:
                    attributes.injector = injector

            return attributes
        else:
            raise DecoratorException("Serializable decorator can only be applied once")

def remove_attributes(cls: type) -> None:
    with SERIALIZABLE_LOCK:
        if cls in SERIALIZABLE_ATTRIBUTES:
            del SERIALIZABLE_ATTRIBUTES[cls]
        else:
            pass # pragma: no cover