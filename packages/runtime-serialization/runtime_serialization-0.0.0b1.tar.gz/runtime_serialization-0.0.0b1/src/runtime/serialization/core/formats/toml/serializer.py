from typing import TypeVar, Any, IO, overload, cast
from io import TextIOBase
from os import path
from toml import loads as load_data, dumps as dump_data

from runtime.serialization.core.base_serializer import BaseSerializer, deserialize as deserialize_base
from runtime.serialization.core.formats.toml.formatter import TomlFormatter
from runtime.serialization.core.interfaces.serializer import Serializer

T = TypeVar('T')

class TomlSerializer(Serializer[T]):
    """The TomlSerializer class is a TOML implementation of the base Serializer class.
    """
    __slots__ = ["__base"]

    def __new__(cls, *args: Any, **kwargs: Any):
        return cast(TomlSerializer[T], super().__new__(cls, *args, **kwargs))

    def __init__(self):
        self.__base = BaseSerializer[self.serializable](TomlFormatter)

    @overload
    def serialize(self, obj: T) -> str:
        """Serializes object as a string.

        Args:
            obj (T): The object to serialize.

        Returns:
            str: Returns a string serialization.
        """
        ...
    @overload
    def serialize(self, obj: T, base: type[Any]) -> str:
        """Serializes object as a string using a more derived base type than T.

        Args:
            obj (T): The object to serialize.
            base (type[T]): The base type.

        Returns:
            str: Returns a string serialization.
        """
        ...
    def serialize(self, obj: T, base: type[Any] | None = None) -> str:
        if base:
            data = self.__base.serialize(obj, base = base)
        else:
            data = self.__base.serialize(obj, base = self.__base.attributes.serializable)

        return dump_data(data)

    @overload
    def dump(self, obj: T, output: TextIOBase | IO[Any], **kwargs: Any) -> None:
        """Serializes object to a file or IO output.

        Args:
            obj (T): The object to serialize.
            output (TextIOBase | IO[Any]): The output.
        """
        ...
    @overload
    def dump(self, obj: T, output: str, *, overwrite: bool = False, **kwargs: Any) -> None:
        """Serializes object to a file.

        Args:
            obj (T): The object to serialize.
            output (str): The path of the output file.
            overwrite (bool): Specifies whether or not to overwrite file if it exists.
        """
        ...
    def dump(self, obj: T, output: TextIOBase | IO[Any] | str, *, overwrite: bool = False, **kwargs: Any) -> None:
        if isinstance(output, str):
            if path.isfile(output) and not overwrite:
                raise FileExistsError
            elif not path.isfile(output):
                with open(output, "a"): # ensure that file exists
                    pass
            with open(output, "wt", encoding = "utf-8") as file:
                serialized = self.serialize(obj)
                file.write(serialized)
        else:
            serialized = self.serialize(obj)
            output.write(serialized)

    def dumps(self, obj: T) -> str:
        """Serializes object to a string.

        Args:
            obj (T): The object to serialize.

        Returns:
            str: Returns a string.
        """
        return self.serialize(obj)


    def deserialize(self, text: str) -> T:
        """Deserializes object from a string.

        Args:
            text (str): The serialization string.

        Returns:
            T: Returns an object.
        """
        data = load_data(text)
        return self.__base.deserialize(data)

    @overload
    def load(self, input: TextIOBase | IO[Any]) -> T:
        """Deserializes object from a file or IO input.

        Args:
            input (TextIOBase | IO[Any]): The input.

        Returns:
            T: Returns an object.
        """
        ...
    @overload
    def load(self, input: str) -> T:
        """Deserializes object from a file.

        Args:
            input (str): The path of the file.

        Returns:
            T: Returns an object.
        """
        ...
    def load(self, input: TextIOBase | IO[Any] | str) -> T:
        if isinstance(input, str):
            if not path.isfile(input):
                raise FileNotFoundError # pragma: no cover
            with open(input, "rt", encoding = "utf-8") as file:
                text = file.read()
                return self.deserialize(text)
        else:
            text = input.read()
            return self.deserialize(text)

    def loads(self, text: str) -> T:
        """Deserializes object from a string.

        Args:
            text (str): The string to deserialize.

        Returns:
            T: Returns an object.
        """
        return self.deserialize(text)



@overload
def serialize(obj: object) -> str:
    """Serializes an object to a TOML string.

    Args:
        obj (object): The object to serialize.

    Returns:
        str: Returns a TOML string.
    """
    ...
@overload
def serialize(obj: T, base: type[T]) -> str:
    """Serializes an object to a TOML string, using the Serializer of a specific base class.
    This is useful when serializing an object, where only the base type is serializable.

    Args:
        obj (T): The object to serialize.
        cls (type[T]): The base class.

    Returns:
        str: Returns a TOML string.
    """
    ...
def serialize(obj: T, base: type[T] | None = None) -> str:
    if base:
        serializer = TomlSerializer[base]()
        return serializer.serialize(obj, base)
    else:
        serializer = TomlSerializer[type(obj)]()
        return serializer.serialize(obj, cast(type[T], object))


@overload
def deserialize(text: str) -> Any:
    """Deserializes a TOML string to an object

    Args:
        text (str): The TOML string to deserialize

    Returns:
        T: Returns an object.
    """
    ...
@overload
def deserialize(text: str, base: type[T]) -> T:
    """Deserializes a TOML string to an object of the specified type

    Args:
        text (str): The TOML string to deserialize
        base (type[T]): The type of serializable to deserialize into

    Returns:
        T: Returns an object.
    """
    ...
def deserialize(text: str, base: type[T] | None = None) -> T | Any:
    if base:
        serializer = TomlSerializer[base]()
        return serializer.deserialize(text)
    else:
        data = load_data(text)
        return deserialize_base(data, None, TomlFormatter)
