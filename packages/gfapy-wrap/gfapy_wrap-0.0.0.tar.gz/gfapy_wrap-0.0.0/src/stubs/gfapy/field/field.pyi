from .parser import Parser as Parser
from .validator import Validator as Validator
from .writer import Writer as Writer
from _typeshed import Incomplete

class Field(Validator, Parser, Writer):
    GFA1_POSFIELD_DATATYPE: Incomplete
    GFA2_POSFIELD_DATATYPE: Incomplete
    GFAX_POSFIELD_DATATYPE: Incomplete
    POSFIELD_DATATYPE: Incomplete
    TAG_DATATYPE: Incomplete
    FIELD_DATATYPE: Incomplete
    FIELD_MODULE: Incomplete
    @classmethod
    def register_datatype(cls, name, klass) -> None: ...
