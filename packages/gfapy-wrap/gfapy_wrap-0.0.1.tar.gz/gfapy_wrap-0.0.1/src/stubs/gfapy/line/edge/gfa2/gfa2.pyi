from ..common.alignment_type import AlignmentType as AlignmentType
from ..common.from_to import FromTo as FromTo
from ..edge import Edge as Edge
from ..gfa2.alignment_type import AlignmentType as GFA2_AlignmentType
from ..gfa2.other import Other as Other
from ..gfa2.references import References as References
from ..gfa2.to_gfa1 import ToGFA1 as ToGFA1
from ..gfa2.validation import Validation as Validation
from _typeshed import Incomplete

class GFA2(Other, References, GFA2_AlignmentType, AlignmentType, FromTo, ToGFA1, Validation, Edge):
    RECORD_TYPE: str
    POSFIELDS: Incomplete
    PREDEFINED_TAGS: Incomplete
    DATATYPE: Incomplete
    NAME_FIELD: str
    FIELD_ALIAS: Incomplete
    REFERENCE_FIELDS: Incomplete
    BACKREFERENCE_RELATED_FIELDS: Incomplete
    DEPENDENT_LINES: Incomplete
