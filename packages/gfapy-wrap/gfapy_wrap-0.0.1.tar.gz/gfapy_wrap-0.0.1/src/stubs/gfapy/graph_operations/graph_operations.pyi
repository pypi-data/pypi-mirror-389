from .artifacts import Artifacts as Artifacts
from .copy_number import CopyNumber as CopyNumber
from .invertible_segments import InvertibleSegments as InvertibleSegments
from .linear_paths import LinearPaths as LinearPaths
from .multiplication import Multiplication as Multiplication
from .p_bubbles import PBubbles as PBubbles
from .redundant_linear_paths import RedundantLinearPaths as RedundantLinearPaths
from .superfluous_links import SuperfluousLinks as SuperfluousLinks
from .topology import Topology as Topology

class GraphOperations(LinearPaths, Multiplication, RedundantLinearPaths, Topology, Artifacts, CopyNumber, InvertibleSegments, PBubbles, SuperfluousLinks): ...
