from .common.cloning import Cloning as Cloning
from .common.connection import Connection as Connection
from .common.construction import Construction as Construction
from .common.default_record_definition import DefaultRecordDefinition as DefaultRecordDefinition
from .common.disconnection import Disconnection as Disconnection
from .common.dynamic_fields import DynamicFields as DynamicFields
from .common.equivalence import Equivalence as Equivalence
from .common.field_data import FieldData as FieldData
from .common.field_datatype import FieldDatatype as FieldDatatype
from .common.update_references import UpdateReferences as UpdateReferences
from .common.validate import Validate as Validate
from .common.version_conversion import VersionConversion as VersionConversion
from .common.virtual_to_real import VirtualToReal as VirtualToReal
from .common.writer import Writer as Writer

class Line(Construction, DynamicFields, Writer, VersionConversion, FieldDatatype, FieldData, Equivalence, Cloning, Connection, VirtualToReal, UpdateReferences, Disconnection, Validate, DefaultRecordDefinition):
    SEPARATOR: str
