from .collections import Collections as Collections
from .creators import Creators as Creators
from .destructors import Destructors as Destructors
from .finders import Finders as Finders
from .headers import Headers as Headers
from _typeshed import Incomplete

class Lines(Collections, Creators, Destructors, Finders, Headers):
    GFA1Specific: Incomplete
    GFA2Specific: Incomplete
