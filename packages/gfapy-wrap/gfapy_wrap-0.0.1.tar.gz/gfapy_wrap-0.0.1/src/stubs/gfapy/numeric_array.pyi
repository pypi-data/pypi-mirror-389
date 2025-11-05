from _typeshed import Incomplete

class NumericArray(list):
    SIGNED_INT_SUBTYPE: Incomplete
    UNSIGNED_INT_SUBTYPE: Incomplete
    INT_SUBTYPE: Incomplete
    FLOAT_SUBTYPE: Incomplete
    SUBTYPE: Incomplete
    SUBTYPE_BITS: Incomplete
    SUBTYPE_RANGE: Incomplete
    def validate(self) -> None: ...
    def compute_subtype(self): ...
    @staticmethod
    def integer_type(range): ...
    @classmethod
    def from_string(cls, string, valid: bool = False): ...
