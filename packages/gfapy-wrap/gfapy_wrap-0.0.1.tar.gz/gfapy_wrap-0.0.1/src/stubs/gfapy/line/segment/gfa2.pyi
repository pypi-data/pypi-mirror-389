from . import Segment as Segment
from .coverage import Coverage as Coverage
from .gfa2_to_gfa1 import GFA2ToGFA1 as GFA2ToGFA1
from .references import References as References
from .writer_wo_sequence import WriterWoSequence as WriterWoSequence
from _typeshed import Incomplete

class GFA2(WriterWoSequence, References, Coverage, GFA2ToGFA1, Segment):
    VERSION: str
    RECORD_TYPE: str
    POSFIELDS: Incomplete
    PREDEFINED_TAGS: Incomplete
    DATATYPE: Incomplete
    NAME_FIELD: str
    FIELD_ALIAS: Incomplete
    DEPENDENT_LINES: Incomplete
