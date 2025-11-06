"""
Unpublished work.
Copyright (c) 2025 by Teradata Corporation. All rights reserved.
TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET

Primary Owner: snigdha.biswas@teradata.com
Secondary Owner: aanchal.kavedia@teradata.com

Version-specific configuration classes for vector store operations
"""

from abc import ABC, abstractmethod
from packaging import version

from teradatagenai.common.constants import (AUGUST_DROP_SIMILARITY_PARAMS, OCTOBER_DROP_SIMILARITY_PARAMS,
                                             AUGUST_DROP_SIMILARITY_SEARCH_URL, OCTOBER_DROP_SIMILARITY_SEARCH_URL)


class _VectorStoreVersionConfig(ABC):
    """
    DESCRIPTION:
        Base class for version-specific configurations.
    """
    
    # Version threshold for configuration switching
    _version_threshold = "1.0.420"
    
    def __init__(self):
        pass
    
    @property
    @abstractmethod
    def similarity_params(self):
        """
        DESCRIPTION:
            Return the similarity parameters for this version.
        
        RETURNS:
            dict
        """
        pass
    
    @property
    def version_threshold(self):
        """
        DESCRIPTION:
            Return the version threshold for configuration switching.
        
        RETURNS:
            str
        """
        return self._version_threshold
    
    @property
    @abstractmethod
    def uses_question_in_url(self):
        """
        DESCRIPTION:
            Return whether this version uses question parameter in URL.
        
        RETURNS:
            bool
        """
        pass
    
    @property
    @abstractmethod
    def similarity_search_url_pattern(self):
        """
        DESCRIPTION:
            Return the URL pattern for similarity search for this version.
        
        RETURNS:
            str
        """
        pass

class _AugustDropConfig(_VectorStoreVersionConfig):
    """
    DESCRIPTION:
        Configuration for August drop versions (< 1.0.420).
    """
    
    def __init__(self):
        super().__init__()
    
    @property
    def similarity_params(self):
        """
        DESCRIPTION:
            Return the similarity parameters for August drop version.
        
        RETURNS:
            dict
        """
        return AUGUST_DROP_SIMILARITY_PARAMS
    
    @property
    def uses_question_in_url(self):
        """
        DESCRIPTION:
            Return whether August drop version uses question parameter in URL.
        
        RETURNS:
            bool
        """
        return True
    
    @property
    def similarity_search_url_pattern(self):
        """
        DESCRIPTION:
            Return the URL pattern for similarity search for August drop version.
        
        RETURNS:
            str
        """
        return AUGUST_DROP_SIMILARITY_SEARCH_URL


class _OctoberDropConfig(_VectorStoreVersionConfig):
    """
    DESCRIPTION:
        Configuration for October drop versions (> 1.0.420).
    """
    
    def __init__(self):
        super().__init__()
    
    @property
    def similarity_params(self):
        """
        DESCRIPTION:
            Return the similarity parameters for October drop version.
        
        RETURNS:
            dict
        """
        return OCTOBER_DROP_SIMILARITY_PARAMS
    
    @property
    def uses_question_in_url(self):
        """
        DESCRIPTION:
            Return whether October drop version uses question parameter in URL.
        
        RETURNS:
            bool
        """
        return False
    
    @property
    def similarity_search_url_pattern(self):
        """
        DESCRIPTION:
            Return the URL pattern for similarity search for October drop version.
        
        RETURNS:
            str
        """
        return OCTOBER_DROP_SIMILARITY_SEARCH_URL

class _VectorStoreVersionFactory:
    """
    DESCRIPTION:
        Internal factory class to get appropriate version configuration.
    """
    
    @classmethod
    def _get_config(cls, session_id):
        """
        DESCRIPTION:
            Return the appropriate version configuration based on current DB version.
        
        PARAMETERS:
            session_id:
                Required Argument.
                Specifies the session ID to get cached health data for.
                Types: str
        
        RETURNS:
            _VectorStoreVersionConfig
        
        RAISES:
            None.
        
        EXAMPLES:
            >>> config = _VectorStoreVersionFactory._get_config(session_id)
            >>> similarity_params = config.similarity_params
            >>> uses_question_in_url = config.uses_question_in_url
        """
        # Import here to avoid circular imports
        from teradatagenai.vector_store.vector_store import VSManager
        
        # Use cached health data for this session (should always be available)
        health_data = VSManager._cached_health_data[session_id]
        current_version = health_data['version'].iloc[0]
        
        # Use version comparison: October Drop is > 1.0.420
        if version.parse(current_version) < version.parse(_VectorStoreVersionConfig._version_threshold):
            return _AugustDropConfig()
        else:
            return _OctoberDropConfig()