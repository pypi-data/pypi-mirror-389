from .dynamic_fields import DynamicField as DynamicField
from _typeshed import Incomplete

class Construction:
    DELAYED_PARSING_DATATYPES: Incomplete
    RECORD_TYPE_VERSIONS: Incomplete
    def __new__(cls, data, vlevel: int = 1, virtual: bool = False, dialect: str = 'standard', version=None): ...
    vlevel: Incomplete
    def __init__(self, data, vlevel: int = 1, virtual: bool = False, version=None, dialect: str = 'standard') -> None: ...
    EXTENSIONS: Incomplete
    @classmethod
    def register_extension(cls, references=[]) -> None: ...
