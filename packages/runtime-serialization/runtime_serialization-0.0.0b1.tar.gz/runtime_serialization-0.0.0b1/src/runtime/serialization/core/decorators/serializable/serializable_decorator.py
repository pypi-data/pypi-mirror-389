from typing import TypeVar, Callable, overload

from runtime.serialization.core.decorators.serializable.serializable_attributes import get_or_set_attributes
from runtime.serialization.core.serializer_attributes import SerializerAttributes
from runtime.serialization.core.interfaces.type_activator import TypeActivator
from runtime.serialization.core.default_type_activator import DefaultTypeActivator
from runtime.serialization.core.interfaces.injector import Injector

T = TypeVar('T')

class SerializableDecorator:

    @staticmethod
    def namespace(value: str) -> Callable[[type[T]], type[T]]:
        """Sets the serializable attribute 'namespace'.

        Args:
            value (str): The namespace.
        """
        def decorate(cls: type[T]) -> type[T]:
            get_or_set_attributes(cls, namespace = value)
            return cls
        return decorate

    @staticmethod
    def strict(value: bool) -> Callable[[type[T]], type[T]]:
        """Sets the serializable attribute 'strict'.

        Args:
            value (bool): Specifies whether or not strict mode is applied.
        """
        def decorate(cls: type[T]) -> type[T]:
            get_or_set_attributes(cls, strict = value)
            return cls
        return decorate

    @staticmethod
    def type_activator(value: type[TypeActivator]) -> Callable[[type[T]], type[T]]:
        """Sets the serializable attribute 'type_activator'

        Args:
            value (type[TypeActivator]): The type activator type.
        """
        def decorate(cls: type[T]) -> type[T]:
            get_or_set_attributes(cls, type_activator = value)
            return cls
        return decorate

    @staticmethod
    def injector(value: type[Injector]) -> Callable[[type[T]], type[T]]:
        """Sets the serializable attribute 'injector'

        Args:
            value (type[Injector]): The injector type.
        """
        def decorate(cls: type[T]) -> type[T]:
            get_or_set_attributes(cls, injector = value)
            return cls
        return decorate

    @overload
    def __call__(self, cls: type[T], /) -> type[T]:
        """Makes the class serializable
        """
        ...
    @overload
    def __call__(
        self, *,
        namespace: str | None = None,
        strict: bool = False,
        type_activator: type[TypeActivator]=DefaultTypeActivator,
    ) -> Callable[[type[T]], type[T]]:
        """Makes the class serializable

        Args:
            namespace (str | None, optional): The class namespace. Defaults to None.
            strict (bool, optional): The strictness. Defaults to False.
            type_activator (type[TypeActivator], optional): The TypeActivator. Defaults to DefaultTypeActivator.
        """
        ...
    @overload
    def __call__(
        self, *,
        namespace: str | None = None,
        strict: bool = False,
        type_activator: type[TypeActivator]=DefaultTypeActivator,
        injector: type[Injector]
    ) -> Callable[[type[T]], type[T]]:
        """Makes the class serializable

        Args:
            namespace (str | None, optional): The class namespace. Defaults to None.
            strict (bool, optional): The strictness. Defaults to False.
            type_activator (type[TypeActivator], optional): The TypeActivator. Defaults to DefaultTypeActivator.
            injector (type[Injector]): The member Injector type.
        """
        ...
    def __call__(
        self,
        cls: type[T] |None = None, *,
        namespace: str | None = None,
        strict: bool | None = None,
        type_activator: type[TypeActivator] | None = None,
        injector: type[Injector] | None = None
    ) -> Callable[[type[T]], type[T]] | type[T]:
        def decorate(cls: type[T]) -> type[T]:
            SerializerAttributes.make_serializable_lazy(
                cls,
                namespace = namespace,
                strict = strict,
                type_activator = type_activator,
                injector = injector
            )
            return cls

        if cls:
            return decorate(cls)
        else:
            return decorate

serializable = SerializableDecorator()