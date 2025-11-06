# pyright: basic
# ruff: noqa

def test_example_1_json():
    from runtime.serialization.json import JsonSerializer, serialize, deserialize
    from runtime.serialization import serializable
    from datetime import date

    @serializable(namespace="tests.examples")
    class Author:
        def __init__(self, name: str, birthday: date):
            self.__name = name
            self.__birthday = birthday

        @property
        def name(self) -> str:
            return self.__name

        @property
        def birthday(self) -> date:
            return self.__birthday

    @serializable(namespace="tests.examples")
    class Book:
        def __init__(self, title: str, author: Author):
            self.__title = title
            self.__author = author

        @property
        def title(self) -> str:
            return self.__title

        @property
        def author(self) -> Author:
            return self.__author

    author = Author("Stephen King", date(1947, 9, 21))
    book = Book("The Shining", author)
    serializer = JsonSerializer[Book]()
    serialized = serializer.serialize(book) # -> {"author": {"birthday": "1947-09-21", "name": "Stephen King"}, "title": "The Shining"}
    deserialized = serializer.deserialize(serialized)
    assert deserialized.author.name == author.name
    assert deserialized.title == book.title

    # same result, different approach without the need for instantiating JsonSerializer manually
    serialized = serialize(book, Book)

    # and without a base type, the type info is embedded
    serialized_untyped = serialize(book) # -> {"author": {"birthday": "1947-09-21", "name": "Stephen King"}, "title": "The Shining", "~type": "tests.examples.Book"}
    deserialized_untyped = deserialize(serialized_untyped)
    assert deserialized_untyped.author.name == deserialized.author.name
    assert deserialized_untyped.title == deserialized.title


def test_example_1_yaml():
    from runtime.serialization.yaml import YamlSerializer
    from runtime.serialization import serializable
    from datetime import date

    @serializable(namespace="tests.examples")
    class Author:
        def __init__(self, name: str, birthday: date):
            self.__name = name
            self.__birthday = birthday

        @property
        def name(self) -> str:
            return self.__name

        @property
        def birthday(self) -> date:
            return self.__birthday

    @serializable(namespace="tests.examples")
    class Book:
        def __init__(self, title: str, author: Author):
            self.__title = title
            self.__author = author

        @property
        def title(self) -> str:
            return self.__title

        @property
        def author(self) -> Author:
            return self.__author

    author = Author("Stephen King", date(1947, 9, 21))
    book = Book("The Shining", author)
    serializer = YamlSerializer[Book]()
    serialized = serializer.serialize(book)
    deserialized = serializer.deserialize(serialized)


def test_example_1_toml():
    from runtime.serialization.toml import TomlSerializer
    from runtime.serialization import serializable
    from datetime import date

    @serializable(namespace="tests.examples")
    class Author:
        def __init__(self, name: str, birthday: date):
            self.__name = name
            self.__birthday = birthday

        @property
        def name(self) -> str:
            return self.__name

        @property
        def birthday(self) -> date:
            return self.__birthday

    @serializable(namespace="tests.examples")
    class Book:
        def __init__(self, title: str, author: Author):
            self.__title = title
            self.__author = author

        @property
        def title(self) -> str:
            return self.__title

        @property
        def author(self) -> Author:
            return self.__author

    author = Author("Stephen King", date(1947, 9, 21))
    book = Book("The Shining", author)
    serializer = TomlSerializer[Book]()
    serialized = serializer.serialize(book)
    deserialized = serializer.deserialize(serialized)


def test_example_1_hjson():
    from runtime.serialization.hjson import HjsonSerializer
    from runtime.serialization import serializable
    from datetime import date

    @serializable(namespace="tests.examples")
    class Author:
        def __init__(self, name: str, birthday: date):
            self.__name = name
            self.__birthday = birthday

        @property
        def name(self) -> str:
            return self.__name

        @property
        def birthday(self) -> date:
            return self.__birthday

    @serializable(namespace="tests.examples")
    class Book:
        def __init__(self, title: str, author: Author):
            self.__title = title
            self.__author = author

        @property
        def title(self) -> str:
            return self.__title

        @property
        def author(self) -> Author:
            return self.__author

    author = Author("Stephen King", date(1947, 9, 21))
    book = Book("The Shining", author)
    serializer = HjsonSerializer[Book]()
    serialized = serializer.serialize(book)
    deserialized = serializer.deserialize(serialized)

def test_example_2_serializable_delegates():
    from typing import Any, Generic, TypeVar, cast
    from typingutils import get_generic_arguments
    from runtime.serialization.json import serialize, deserialize
    from runtime.serialization import serializable, serializable_delegate

    T = TypeVar("T")

    @serializable_delegate
    class TestDelegate(Generic[T]):
        __test__ = False

        def __init__(self):
            self.__type = get_generic_arguments(self)
            self.__shim = None
            self.__data: T | None = None

        @staticmethod
        def create(value_type: type[T]) -> T:
            return cast(T, TestDelegate[value_type]())

        def __get__(self, instance: type | object, cls: type[Any]) -> 'TestDelegate[T]' | T:
            if isinstance(instance, type) and issubclass(instance, cls):
                return self
            else:
                return cast(T, self.__data)

        def __set__(self, instance: object, value: T) -> None:
            self.__data = value

    @serializable(namespace="tests.examples")
    class TestClass:
        def __init__(self, text: str, extended_text: str):
            self.__text = text
            self.extended_text = extended_text

        extended_text = TestDelegate.create(str)

        @property
        def text(self) -> str:
            return self.__text

        @text.setter
        def text(self, value: str) -> None:
            self.__text = value

    test = TestClass("Test", "Extended")
    serialized = serialize(test, TestClass)
    deserialized = deserialize(serialized, TestClass)
    reserialized = serialize(deserialized, TestClass)
    assert serialized == reserialized


def test_example_3_resolvable():
    from typing import Any, Literal
    from runtime.serialization.json import serialize, deserialize
    from runtime.serialization import KwargsTypeActivator, serializable, resolvable, resolve_as

    @serializable(type_activator=KwargsTypeActivator)
    @resolvable
    class Base:
        def __init__(self, **kwargs: Any):
            self.__subtype = kwargs["subtype"]
            self.__prop1 = kwargs["prop1"]

        @property
        def subtype(self) -> Literal["Sub1", "Sub2"]:
            return self.__subtype

        @property
        def prop1(self) -> str:
            return self.__prop1

    @resolve_as(Base, lambda base: base.subtype == "Sub1")
    @serializable(type_activator=KwargsTypeActivator)
    class Sub1(Base):
        def __init__(self, **kwargs: Any):
            super().__init__(**{ **kwargs, "subtype": "Sub1" })
            self.__prop2 = kwargs["prop2"]

        @property
        def prop2(self) -> int:
            return self.__prop2

    @resolve_as(Base, lambda base: base.subtype == "Sub2")
    @serializable(type_activator=KwargsTypeActivator)
    class Sub2(Base):
        def __init__(self, **kwargs: Any):
            super().__init__(**{ **kwargs, "subtype": "Sub2" })
            self.__prop2 = kwargs["prop2"]
            self.__prop3 = kwargs["prop3"]

        @property
        def prop2(self) -> int:
            return self.__prop2

        @property
        def prop3(self) -> bool:
            return self.__prop3


    test1 = Sub1(prop1  = "Test", prop2 = 1)
    serialized = serialize(test1, Base)
    deserialized = deserialize(serialized, Base)
    assert deserialized.subtype == test1.subtype
    assert deserialized.prop1 == test1.prop1
    assert isinstance(deserialized, Sub1)
    assert deserialized.prop2 == test1.prop2
    reserialized = serialize(deserialized, Base)
    assert serialized == reserialized

    test2 = Sub2(prop1  = "Test", prop2 = 2, prop3 = True)
    serialized = serialize(test2, Base)
    deserialized = deserialize(serialized, Base)
    assert deserialized.subtype == test2.subtype
    assert deserialized.prop1 == test2.prop1
    assert isinstance(deserialized, Sub2)
    assert deserialized.prop2 == test2.prop2
    assert deserialized.prop3 == test2.prop3
    reserialized = serialize(deserialized, Base)
    assert serialized == reserialized
