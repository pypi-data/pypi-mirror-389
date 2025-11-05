from ..common.alignment_type import AlignmentType as AlignmentType
from ..common.from_to import FromTo as FromTo
from ..edge import Edge as Edge
from ..gfa1.alignment_type import AlignmentType as GFA1_AlignmentType
from ..gfa1.oriented_segments import OrientedSegments as OrientedSegments
from ..gfa1.other import Other as Other
from ..gfa1.references import References as GFA1_References
from ..gfa1.to_gfa2 import ToGFA2 as GFA1_ToGFA2
from .canonical import Canonical as Canonical
from .complement import Complement as Complement
from .equivalence import Equivalence as Equivalence
from .references import References as Link_References
from .to_gfa2 import ToGFA2 as Link_ToGFA2
from _typeshed import Incomplete

class Link(Link_ToGFA2, GFA1_ToGFA2, Link_References, Equivalence, Complement, Canonical, Other, GFA1_AlignmentType, OrientedSegments, GFA1_References, AlignmentType, FromTo, Edge):
    RECORD_TYPE: str
    POSFIELDS: Incomplete
    PREDEFINED_TAGS: Incomplete
    DATATYPE: Incomplete
    NAME_FIELD: str
    REFERENCE_FIELDS: Incomplete
    BACKREFERENCE_RELATED_FIELDS: Incomplete
    DEPENDENT_LINES: Incomplete
