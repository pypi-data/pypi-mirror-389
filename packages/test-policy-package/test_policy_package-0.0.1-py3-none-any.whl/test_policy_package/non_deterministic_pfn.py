from typing import Optional

import rucio.common.utils


class YourVONonDeterministicPFNAlgorithm(rucio.common.utils.NonDeterministicPFNAlgorithms):
    """
    Your VO specific non-deterministic PFN algorithm
    """

    def __init__(self):
        super().__init__()

    @classmethod
    def _module_init_(cls) -> None:
        """
        Registers the included non-deterministic PFN algorithms
        """
        cls.register('yourvo', cls.construct_non_deterministic_pfn_yourvo)

    @staticmethod
    def construct_non_deterministic_pfn_yourvo(dsn: str, scope: Optional[str], filename: str) -> str:
        fields = dsn.split("/")
        nfields = len(fields)
        if nfields == 0:
            return '/other/%s' % (filename)
        else:
            return '%s/%s' % (dsn, filename)
        
YourVONonDeterministicPFNAlgorithm._module_init_()