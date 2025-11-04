from enum import StrEnum


class Sensitivity(StrEnum):
    """
    Represents a classification system for sensitivity levels of data.

    Attributes:
        HIGHLY_SENSITIVE: Represents highly sensitive data, such as private or
            critical information.
        CONFIDENTIAL: Represents confidential data that requires restricted
            access.
        IDENTIFIABLE: Represents data that can directly identify individuals.
        POTENTIALLY_IDENTIFIABLE: Represents data that may not directly identify
            an individual but could do so when combined with other information.
        LIMITED: Operational or administrative data with minimal personal
            information but still requires protection.
        NON_SENSITIVE: Non-identifiable metadata or system information that
            poses minimal privacy risk
        UNKNOWN: Represents data with an unknown or undefined level of
            sensitivity.
    """

    HIGHLY_SENSITIVE = "1_highly_sensitive"
    CONFIDENTIAL = "2_confidential"
    IDENTIFIABLE = "3_identifiable"
    POTENTIALLY_IDENTIFIABLE = "4_potentially_identifiable"
    LIMITED = "5_limited"
    NON_SENSITIVE = "6_non_sensitive"
    UNKNOWN = "99_unknown"
