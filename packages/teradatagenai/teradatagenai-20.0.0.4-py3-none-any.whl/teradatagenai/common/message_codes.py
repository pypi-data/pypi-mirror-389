# ##################################################################
#
# Copyright 2025 Teradata. All rights reserved.
# TERADATA CONFIDENTIAL AND TRADE SECRET
#
# Primary Owner: Snigdha Biswas (snigdha.biswas@teradata.com)
# Secondary Owner: Aanchal Kavedia (aanchal.kavedia@teradata.com)
#
# Notes:
#   * This code is only for internal use.
#   * This file includes the teradatgenai error codes.
#
# ##################################################################
class MessageCodes:
    """
    Class to store message codes for the teradatagenai package.
    """
    # General Codes TDGENAI_2001 - TDGENAI_2100
    INVALID_FUNCTION_PARAMETER = "TDGENAI_2001"
    ATTRIBUTE_UNAVAILABLE = "TDGENAI_2002"
    RESERVED_KEYWORD = "TDGENAI_2003"
    # Text Analytics Codes TDGENAI_2101 - TDGENAI_2200
    METHOD_NOT_IMPLEMENTED = "TDGENAI_2101"
    # Vector Store Codes TDGENAI_2201 - TDGENAI_2300
    VS_PRESENT = "TDGENAI_2201"