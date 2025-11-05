from _typeshed import Incomplete

class DynamicField:
    get: Incomplete
    set: Incomplete
    def __init__(self, get, set) -> None: ...

class DynamicFields:
    def __getattribute__(self, name): ...
    def __setattr__(self, name, value): ...
