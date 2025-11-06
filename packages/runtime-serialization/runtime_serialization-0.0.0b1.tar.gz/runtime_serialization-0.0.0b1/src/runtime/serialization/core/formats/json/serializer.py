from typing import TypeVar, overload, Any, cast, IO
from io import TextIOBase
from os import path
from json import loads as load_data, dumps as dump_data

from runtime.serialization.core.base_serializer import BaseSerializer, deserialize as deserialize_base
from runtime.serialization.core.formats.json.formatter import JsonFormatter
from runtime.serialization.core.interfaces.serializer import Serializer

T = TypeVar('T')

class JsonSerializer(Serializer[T]):
    """The JsonSerializer class is a JSON implementation of the base Serializer class.
    """
    __slots__ = ["__base"]

    def __new__(cls, *args: Any, **kwargs: Any):
        return cast(JsonSerializer[T], super().__new__(cls, *args, **kwargs))

    def __init__(self):
        self.__base = BaseSerializer[self.serializable](JsonFormatter)

    @overload
    def serialize(self, obj: T, *, pretty_print: bool = False) -> str:
        """Serializes object as a string.

        Args:
            obj (T): The object to serialize.

        Returns:
            str: Returns a string serialization.
        """
        ...
    @overload
    def serialize(self, obj: T, base: type[Any], *, pretty_print: bool = False) -> str:
        """Serializes object as a string using a more derived base type than T.

        Args:
            obj (T): The object to serialize.
            base (type[T]): The base type.

        Returns:
            str: Returns a string serialization.
        """
        ...
    def serialize(self, obj: T, base: type[Any] | None = None, *, pretty_print: bool = False) -> str:
        if base:
            data = self.__base.serialize(obj, base = base)
        else:
            data = self.__base.serialize(obj, base = self.__base.attributes.serializable)

        if pretty_print:
            return dump_data(data, indent = 4, sort_keys=True)
        else:
            return dump_data(data, indent = None)


    @overload
    def dump(self, obj: T, output: TextIOBase | IO[Any], *, pretty_print: bool = True, **kwargs: Any) -> None:
        """Serializes object to a file or IO output.

        Args:
            obj (T): The object to serialize.
            output (TextIOBase | IO[Any]): The output.
            pretty_print (bool, optional): Specifies whether or not to output indentations. Defaults to True.
        """
        ...
    @overload
    def dump(self, obj: T, output: str, *, overwrite: bool = False, pretty_print: bool = True, **kwargs: Any) -> None:
        """Serializes object to a file.

        Args:
            obj (T): The object to serialize.
            output (str): The path of the output file.
            overwrite (bool): Specifies whether or not to overwrite file if it exists.
            pretty_print (bool, optional): Specifies whether or not to output indentations. Defaults to True.
        """
        ...
    def dump(self, obj: T, output: TextIOBase | IO[Any] | str, *, overwrite: bool = False, pretty_print: bool = True, **kwargs: Any) -> None:
        if isinstance(output, str):
            if path.isfile(output) and not overwrite:
                raise FileExistsError
            elif not path.isfile(output):
                with open(output, "a"): # ensure that file exists
                    pass
            with open(output, "wt", encoding = "utf-8") as file:
                serialized = self.serialize(obj, pretty_print = pretty_print)
                file.write(serialized)
        else:
            serialized = self.serialize(obj, pretty_print = pretty_print)
            output.write(serialized)

    def dumps(self, obj: T, *, pretty_print: bool = True) -> str:
        """Serializes object to a string.

        Args:
            obj (T): The object to serialize.
            pretty_print (bool, optional): Specifies whether or not to output indentations. Defaults to True.

        Returns:
            str: Returns a string.
        """
        return self.serialize(obj, pretty_print = pretty_print)


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
    """Serializes an object to a JSON string

    Args:
        obj (object): The object to serialize

    Returns:
        str: Returns a JSON string
    """
    ...
@overload
def serialize(obj: T, base: type[T]) -> str:
    """Serializes an object to a JSON string, using the Serializer of a specific base class.
    This is useful when serializing an object, where only the base type is serializable.

    Args:
        obj (T): The object to serialize.
        base (type[T]): The base class.

    Returns:
        str: Returns a JSON string.
    """
    ...
def serialize(obj: T, base: type[T] | None = None) -> str:
    if base:
        serializer = JsonSerializer[base]()
        return serializer.serialize(obj, base)
    else:
        serializer = JsonSerializer[type(obj)]()
        return serializer.serialize(obj, cast(type[T], object))


@overload
def deserialize(text: str) -> Any:
    """Deserializes a JSON string to an object

    Args:
        text (str): The JSON string to deserialize

    Returns:
        T: Returns an object.
    """
    ...
@overload
def deserialize(text: str, base: type[T]) -> T:
    """Deserializes a JSON string to an object of the specified type.

    Args:
        text (str): The JSON string to deserialize.
        base (type[T]): The type of serializable to deserialize into.

    Returns:
        T: Returns an object.
    """
    ...
def deserialize(text: str, base: type[T] | None = None) -> T | Any:
    if base:
        serializer = JsonSerializer[base]()
        return serializer.deserialize(text)
    else:
        data = load_data(text)
        return deserialize_base(data, None, JsonFormatter)
