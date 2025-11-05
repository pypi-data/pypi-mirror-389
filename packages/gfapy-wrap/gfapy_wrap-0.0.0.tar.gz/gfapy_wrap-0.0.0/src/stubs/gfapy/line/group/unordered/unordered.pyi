from ..gfa2.references import References as References
from ..gfa2.same_id import SameID as SameID
from ..group import Group as Group
from ..unordered.induced_set import InducedSet as InducedSet
from ..unordered.references import References as UnorderedReferences
from _typeshed import Incomplete

class Unordered(UnorderedReferences, InducedSet, References, SameID, Group):
    RECORD_TYPE: str
    POSFIELDS: Incomplete
    FIELD_ALIAS: Incomplete
    DATATYPE: Incomplete
    NAME_FIELD: str
    REFERENCE_FIELDS: Incomplete
    DEPENDENT_LINES: Incomplete
