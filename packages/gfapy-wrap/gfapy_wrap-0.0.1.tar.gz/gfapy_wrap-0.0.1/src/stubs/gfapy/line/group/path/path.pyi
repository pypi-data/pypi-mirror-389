from ..group import Group as Group
from .captured_path import CapturedPath as CapturedPath
from .references import References as References
from .to_gfa2 import ToGFA2 as ToGFA2
from .topology import Topology as Topology
from .validation import Validation as Validation
from _typeshed import Incomplete

class Path(Topology, References, Validation, CapturedPath, ToGFA2, Group):
    RECORD_TYPE: str
    POSFIELDS: Incomplete
    FIELD_ALIAS: Incomplete
    DATATYPE: Incomplete
    NAME_FIELD: str
    REFERENCE_FIELDS: Incomplete
    OTHER_REFERENCES: Incomplete
