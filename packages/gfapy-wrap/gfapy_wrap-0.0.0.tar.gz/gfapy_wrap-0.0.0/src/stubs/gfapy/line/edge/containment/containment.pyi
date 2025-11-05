from ..common.alignment_type import AlignmentType as AlignmentType
from ..common.from_to import FromTo as FromTo
from ..containment.canonical import Canonical as Canonical
from ..containment.pos import Pos as Pos
from ..containment.to_gfa2 import ToGFA2 as Containment_ToGFA2
from ..edge import Edge as Edge
from ..gfa1.alignment_type import AlignmentType as GFA1_AlignmentType
from ..gfa1.oriented_segments import OrientedSegments as OrientedSegments
from ..gfa1.other import Other as Other
from ..gfa1.references import References as References
from ..gfa1.to_gfa2 import ToGFA2 as GFA1_ToGFA2
from _typeshed import Incomplete

class Containment(Containment_ToGFA2, Pos, Canonical, Other, GFA1_AlignmentType, OrientedSegments, References, GFA1_ToGFA2, AlignmentType, FromTo, Edge):
    RECORD_TYPE: str
    POSFIELDS: Incomplete
    FIELD_ALIAS: Incomplete
    PREDEFINED_TAGS: Incomplete
    NAME_FIELD: str
    DATATYPE: Incomplete
    REFERENCE_FIELDS: Incomplete
