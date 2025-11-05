from _typeshed import Incomplete

from ..line import Line as Line
from .construction import Construction as Construction
from .tags import Tags as Tags
from .version_conversion import VersionConversion as VersionConversion
from .writer import Writer as Writer

class Comment(  # type: ignore[misc]
    Writer,
    Tags,
    Construction,
    VersionConversion,
    Line,
):
    RECORD_TYPE: str
    POSFIELDS: Incomplete
    DATATYPE: Incomplete
