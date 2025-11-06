from typing import Any
from typingutils import AnyType

from runtime.serialization.core.helpers import Result
from runtime.serialization.core.primitives import Primitives
from runtime.serialization.core.base_formatter import BaseFormatter
from runtime.serialization.core.interfaces.formatter import Formatter as FormatterBase

class HjsonFormatter(FormatterBase):
    """The HjsonFormatter class extends the base formatter with HJSON specific formatting where applicable.
    """

    def encode(self, value: Any, member_type: AnyType | None) -> Result[Primitives]:
        """Encodes a value to a primitive form (booleans, integers, floats, strings, lists and dicts).

        Args:
            value (Any): The value to be encoded.
            member_type (AnyType | None): The member type specified by the model.

        Returns:
            Result[Primitives]: Returns a primitive value result.
        """
        return BaseFormatter.encode(value, member_type)

    def decode(self, value: Primitives, member_type: AnyType | None) -> Result[Any]:
        """Decodes a value from a primitive form (booleans, integers, floats, strings, lists and dicts).

        Args:
            value (Primitives): The value to be decoded.
            member_type (AnyType | None): The member type specified by the model.

        Returns:
            Result[Any]: Returns a value result.
        """
        return BaseFormatter.decode(value, member_type)

