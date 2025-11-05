from . import Segment as Segment
from .coverage import Coverage as Coverage
from .gfa1_to_gfa2 import GFA1ToGFA2 as GFA1ToGFA2
from .length_gfa1 import LengthGFA1 as LengthGFA1
from .references import References as References
from .writer_wo_sequence import WriterWoSequence as WriterWoSequence
from _typeshed import Incomplete

class GFA1(WriterWoSequence, References, Coverage, LengthGFA1, GFA1ToGFA2, Segment):
    VERSION: str
    RECORD_TYPE: str
    POSFIELDS: Incomplete
    PREDEFINED_TAGS: Incomplete
    DATATYPE: Incomplete
    NAME_FIELD: str
    FIELD_ALIAS: Incomplete
    DEPENDENT_LINES: Incomplete
    gfa2_compatibility: Incomplete
    OTHER_REFERENCES = gfa2_compatibility
