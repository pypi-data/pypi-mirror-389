from ..line import Line as Line
from _typeshed import Incomplete

class Unknown(Line):
    RECORD_TYPE: str
    POSFIELDS: Incomplete
    DATATYPE: Incomplete
    NAME_FIELD: str
    DEPENDENT_LINES: Incomplete
    @property
    def virtual(self): ...
