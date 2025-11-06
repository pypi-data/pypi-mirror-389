try:
    import yaml as _ # noqa: F401
except ModuleNotFoundError: # pragma: no cover
    raise ModuleNotFoundError("Package PyYAML is required, to use runtime.serialization.yaml namespace")

from runtime.serialization.core.formats.yaml.formatter import YamlFormatter
from runtime.serialization.core.formats.yaml.serializer import YamlSerializer, serialize, deserialize

__all__ = [
    'YamlFormatter',
    'YamlSerializer',
    'serialize',
    'deserialize'
]