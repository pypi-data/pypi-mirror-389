from typingutils import AnyType, get_type_name

class NotSerializableException(Exception):
    """The NotSerializableException is an exceptiuon thrown during serialization
    when a particular type is not serializable.
    """
    def __init__(self, cls: AnyType, msg: str | None = None):
        if msg is None:
            super().__init__(f"Type {get_type_name(cls)} is not serializable")
        else:
            super().__init__(f"Type {get_type_name(cls)} is not serializable: {msg}")
