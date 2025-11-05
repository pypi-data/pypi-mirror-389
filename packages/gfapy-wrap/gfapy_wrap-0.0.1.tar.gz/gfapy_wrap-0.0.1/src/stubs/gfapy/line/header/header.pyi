from ..line import Line as Line
from .connection import Connection as Connection
from .field_data import FieldData as FieldData
from .multiline import Multiline as Multiline
from .version_conversion import VersionConversion as VersionConversion
from _typeshed import Incomplete

class Header(VersionConversion, Multiline, Connection, FieldData, Line):
    RECORD_TYPE: str
    PREDEFINED_TAGS: Incomplete
    DATATYPE: Incomplete
    STORAGE_KEY: str
