from ..line import Line as Line
from .references import References as References
from _typeshed import Incomplete

class Gap(References, Line):
    RECORD_TYPE: str
    POSFIELDS: Incomplete
    FIELD_ALIAS: Incomplete
    NAME_FIELD: str
    STORAGE_KEY: str
    DATATYPE: Incomplete
    REFERENCE_FIELDS: Incomplete
