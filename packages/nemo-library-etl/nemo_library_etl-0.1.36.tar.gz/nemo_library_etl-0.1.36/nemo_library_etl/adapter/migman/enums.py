from enum import Enum


class MigManExtractAdapter(Enum):
    GENERICODBC = "genericodbc"
    INFORCOM = "inforcom"
    SAPECC = "sapecc"
    PROALPHA = "proalpha"
    SAGEKHK = "sagekhk"


class MigManTransformStep(Enum):
    JOINS = "10_joins"
    MAPPINGS = "20_mappings"
    DUPLICATES = "30_duplicates"
    NEWNUMBERS = "40_newnumbers"
    NONEMPTY = "50_nonempty"
