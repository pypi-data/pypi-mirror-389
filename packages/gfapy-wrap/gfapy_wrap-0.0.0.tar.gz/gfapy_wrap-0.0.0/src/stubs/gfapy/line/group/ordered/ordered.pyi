from .. import Group as Group
from ..gfa2.references import References as GFA2_References
from ..gfa2.same_id import SameID as SameID
from .captured_path import CapturedPath as CapturedPath
from .references import References as Ordered_References
from .to_gfa1 import ToGFA1 as ToGFA1
from _typeshed import Incomplete

class Ordered(Ordered_References, CapturedPath, GFA2_References, SameID, ToGFA1, Group):
    RECORD_TYPE: str
    POSFIELDS: Incomplete
    FIELD_ALIAS: Incomplete
    DATATYPE: Incomplete
    NAME_FIELD: str
    REFERENCE_FIELDS: Incomplete
    DEPENDENT_LINES: Incomplete
