from ..line import Line as Line
from .references import References as References
from .validation import Validation as Validation
from _typeshed import Incomplete

class Fragment(References, Validation, Line):
    RECORD_TYPE: str
    POSFIELDS: Incomplete
    PREDEFINED_TAGS: Incomplete
    STORAGE_KEY: str
    DATATYPE: Incomplete
    REFERENCE_FIELDS: Incomplete
