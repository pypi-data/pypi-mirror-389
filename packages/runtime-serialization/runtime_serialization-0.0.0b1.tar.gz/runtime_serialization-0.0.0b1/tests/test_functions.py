# pyright: basic
# ruff: noqa
from typing import TypeVar, Any, Annotated, Literal, cast
from pytest import raises as assert_raises

from runtime.serialization import (
    is_serializable, make_serializable, serializable, ignore, resolve_as, resolvable,
    DefaultTypeActivator, KwargsTypeActivator, BaseSerializer, Member,
    DeserializationException, SerializationException, NotSerializableException, CircularReferenceException
)
from runtime.serialization.interfaces import Injector
from runtime.serialization.core.shared import check_serializable

T = TypeVar('T')

def test_is_serializable(serializable_types: list[type[Any]], serializables: list[Any]):
    from tests.classes.generic_type import GenericType

    assert not is_serializable(GenericType)
    assert not is_serializable(NotSerializableClass())
    # assert is_serializable(tuple[str])
    # assert is_serializable(tuple[str, ...])
    # assert is_serializable(tuple[str, int])


    for obj in serializables:
        assert is_serializable(obj)

    for cls in serializable_types:
        assert is_serializable(cls)

    assert is_serializable(Annotated[str, "some string"])
    assert is_serializable(Literal[1, "b", True])
    assert not is_serializable(Literal[1, NotSerializableClass()])

def test_check_serializable(serializable_types: list[type[Any]], serializables: list[Any]):
    from tests.classes.generic_type import GenericType

    with assert_raises(NotSerializableException):
        check_serializable(GenericType)

    with assert_raises(NotSerializableException):
        check_serializable(NotSerializableClass)

    for cls in serializable_types:
        check_serializable(cls)


def test_make_serializable():
    # Test1NoAttributes requires KwargsTypeActivator
    with assert_raises(NotSerializableException, match = r"Type .* is not serializable: DefaultTypeActivator cannot deserialize type"):
        make_serializable(Test1NoAttributes)

    make_serializable(Test1NoAttributes, type_activator = KwargsTypeActivator)

    with assert_raises(NotSerializableException, match = r"Type .* is not serializable: KwargsTypeActivator cannot deserialize type"):
        make_serializable(Test2NoAttributes, type_activator = KwargsTypeActivator)


    # Test2NoAttributes only requires DefaultTypeActivator
    make_serializable(Test2NoAttributes)

    for cls in (Test1, Test2):
        make_serializable(cls)

    for cls in (Test1, Test2):
        with assert_raises(Exception, match = "Serializable decorator can only be applied once"):
            make_serializable(cls)




@serializable.namespace("test")
@serializable.strict(True)
@serializable.type_activator(KwargsTypeActivator)
class Test1:
    __test__ = False
    def __init__(self, **kwargs: Any):
        self.__prop1 = kwargs["prop1"]

    @property
    def prop1(self) -> int:
        return self.__prop1

class Test1NoAttributes:
    __test__ = False
    def __init__(self, **kwargs: Any):
        self.__prop1 = kwargs["prop1"]

    @property
    def prop1(self) -> int:
        return self.__prop1

@serializable.namespace("test")
@serializable.type_activator(DefaultTypeActivator)
@serializable.strict(True)
class Test2:
    __test__ = False
    def __init__(self, prop1: int):
        self.__prop1 = prop1

    @property
    def prop1(self) -> int:
        return self.__prop1

class Test2NoAttributes:
    __test__ = False
    def __init__(self, prop1: int):
        self.__prop1 = prop1

    @property
    def prop1(self) -> int:
        return self.__prop1

class NotSerializableClass:
    __test__ = False
    pass



@serializable.type_activator(DefaultTypeActivator)
@serializable.strict(True)
@serializable.namespace("test")
class Test3:
    __test__ = False
    def __init__(self, prop1: int):
        self.__prop1 = prop1

    @property
    def prop1(self) -> int:
        return self.__prop1