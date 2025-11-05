from ..core import ParaO

# alternative parameter ordering


class DefinitionOrder(ParaO):
    @classmethod
    def __dir__(self): ...


class CreationORder(ParaO):
    @classmethod
    def __dir__(self):
        orig = super().__dir__()
