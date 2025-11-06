from typing import Any, cast
from typingutils import AnyType, issubclass_typing
from collections.abc import Sequence, Mapping

from runtime.serialization.core.helpers import Result
from runtime.serialization.core.primitives import Primitives
from runtime.serialization.core.base_formatter import BaseFormatter
from runtime.serialization.core.interfaces.formatter import Formatter as FormatterBase

class TomlFormatter(FormatterBase):
    """The TomlFormatter class extends the base formatter with TOML specific formatting where applicable.
    """

    def encode(self, value: Any, member_type: AnyType | None) -> Result[Primitives]:
        """Encodes a value to a primitive form (booleans, integers, floats, strings, lists and dicts).

        Args:
            value (Any): The value to be encoded.
            member_type (AnyType | None): The member type specified by the model.

        Returns:
            Result[Primitives]: Returns a primitive value result.
        """
        if isinstance(value, Sequence) and not is_homogenous_list(cast(Sequence[Any], value)):
            padding = len(str(len(cast(Sequence[Any], value))))
            return {
                f"{index:0{padding+1}}" : item
                for index, item in enumerate(cast(Sequence[Any], value))
            }, True
        else:
            return BaseFormatter.encode(value, member_type)


    def decode(self, value: Primitives, member_type: AnyType | None) -> Result[Any]:
        """Decodes a value from a primitive form (booleans, integers, floats, strings, lists and dicts).

        Args:
            value (Primitives): The value to be decoded.
            member_type (AnyType | None): The member type specified by the model.

        Returns:
            Result[Any]: Returns a value result.
        """
        if isinstance(value, dict) and member_type and issubclass_typing(member_type, (list, tuple)):
            return list(cast(Mapping[str, Any], value).values()), True
        else:
            return BaseFormatter.decode(value, member_type)


def is_homogenous_list(value: Sequence[Any]) -> bool:
    """Checks if list is homogenous i.e. containing items of the same type.
    This is a TOML reauirement.

    Args:
        value (Sequence[Any]): The list to check.

    Returns:
        bool: Returns True if list is homogenous.
    """
    last_type: AnyType | None = None
    for item in value:
        this_type = cast(AnyType, type(item))
        if last_type is not None and last_type != this_type:
            return False
        last_type = this_type
    return True
