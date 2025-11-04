"""
Example of a default algorithm - no class needed here, just a function called lfn2pfn.
"""
def lfn2pfn(scope, name, rse, rse_attrs, protocol_attrs):
    """
    :param scope: Scope of the LFN.
    :param name: File name of the LFN.
    :param rse: RSE for PFN
    :param rse_attrs: RSE attributes for PFN
    :param protocol_attrs: RSE protocol attributes for PFN
    :returns: Path for use in the PFN generation.
    """
    return name