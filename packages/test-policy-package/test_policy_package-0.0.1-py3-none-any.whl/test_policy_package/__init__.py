SUPPORTED_VERSION = [">=35.0.0"] # Specify the Rucio versions supported by this policy package

def get_algorithms():
    from test_policy_package.non_deterministic_pfn import YourVONonDeterministicPFNAlgorithm
    from test_policy_package.scope import YourVOScopeExtractionAlgorithm
    from test_policy_package.pfn2lfn import YourVORSEDeterministicScopeTranslation
    from test_policy_package.tape_metadata import YourVOTapeMetadataPlugin
    return { 
        'non_deterministic_pfn': {
            'yourvo_non_deterministic_pfn': YourVONonDeterministicPFNAlgorithm.construct_non_deterministic_pfn_yourvo
            },
        'pfn2lfn': {
            'yourvo_pfn2lfn': YourVORSEDeterministicScopeTranslation.pfn2lfn_yourvo
            },
        'scope': { 
            'yourvo_extract_scope': YourVOScopeExtractionAlgorithm.extract_scope_yourvo
            },
        'fts3_tape_metadata_plugins': {
            'yourvo_tape_metadata': YourVOTapeMetadataPlugin.get_archive_metadata
        }
    }