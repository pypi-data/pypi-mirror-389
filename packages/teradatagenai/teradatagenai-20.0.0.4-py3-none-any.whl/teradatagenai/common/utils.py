"""
Copyright (c) 2025 by Teradata Corporation. All rights reserved.
TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET

Primary Owner: snigdha.biswas@teradata.com
Secondary Owner: PankajVinod.Purandare@Teradata.com

This is a common class to include common functionality required
by other classes which can be reused according to the need.
"""  
from ..telemetry_utils.queryband import session_queryband
from teradataml.utils.utils import execute_sql

class GenAIUtilFuncs():
    """Utility functions for teradatagenai package."""

    @staticmethod
    def _set_queryband():
        try:
            qb_query = session_queryband.generate_set_queryband_query()
            execute_sql(qb_query)
        except Exception as _set_queryband_err:
            pass