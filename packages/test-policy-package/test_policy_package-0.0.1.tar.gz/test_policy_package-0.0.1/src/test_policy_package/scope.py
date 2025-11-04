from typing import TYPE_CHECKING, Optional

import rucio.common.utils

if TYPE_CHECKING:
    from collections.abc import Sequence

class YourVOScopeExtractionAlgorithm(rucio.common.utils.ScopeExtractionAlgorithms):
    def __init__(self) -> None:
        """
        Initialises scope extraction algorithm object
        """
        super().__init__()

    @classmethod
    def _module_init_(cls) -> None:
        """
        Registers the included scope extraction algorithms
        """
        cls.register('yourvo', cls.extract_scope_yourvo)

    @staticmethod
    def extract_scope_yourvo(did: str, scopes: Optional['Sequence[str]']) -> 'Sequence[str]':
        return 'other', did


YourVOScopeExtractionAlgorithm._module_init_()