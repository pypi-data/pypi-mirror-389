# -*- coding: utf-8 -*-
"""
Unpublished work.
Copyright (c) 2025 by Teradata Corporation. All rights reserved.
TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET

Primary Owner: aanchal.kavedia@teradata.com
Secondary Owner: PankajVinod.Purandare@teradata.com

teradatagenai.common.constants
----------
A class for holding all constants
"""
from enum import Enum
from teradataml.options.configure import configure
from teradataml.common.constants import HTTPRequest
from teradataml.common.utils import UtilFuncs
from teradataml.utils.validators import _Validators
from teradatasqlalchemy.types import INTEGER, VARCHAR, VECTOR, CLOB

class Action(Enum):
    # Holds variable names for the type of grant to be provided.
    GRANT = "GRANT"
    REVOKE = "REVOKE"

class Permission(Enum):
    # Holds variable names for the type of permission to be provided.
    USER = "USER"
    ADMIN = "ADMIN"

class VSApi(Enum):
    # Holds variable names for the type of API to be used.
    Ask = "ask"
    PrepareResponse = "prepare-response"
    SimilaritySearch = "similarity-search"

class NVIngestSchemaColumns(Enum):
    """
    Enum for NVIDIA NV-Ingest compatible vector store schema column definitions.
    
    This enum defines the standard column names and their corresponding data types
    for creating vector stores compatible with NVIDIA NV-Ingest processing pipeline.
    """
    # Column name constants
    TD_ID = "TDID"
    TD_FILENAME = "TD_FILENAME"
    text = "text"
    EMBEDDINGS = "embeddings"
    
    @classmethod
    def get_dtype_mapping(cls):
        """
        Get the complete data type mapping for NV-Ingest schema.
        
        Returns:
            Dict[str, Any]: Dictionary mapping column names to their SQLAlchemy types.
        """
        return {
            cls.TD_ID.value: INTEGER(),
            cls.TD_FILENAME.value: VARCHAR(10000),
            cls.text.value: VARCHAR(32000, charset='Unicode'),
            cls.EMBEDDINGS.value: VECTOR()
        }

class VectorStoreURLs:
    # Class to store the vector store URLs
    @property
    def base_url(self):
        return f"{configure._vector_store_base_url}/api/v1/"

    @property
    def session_url(self):
        return f"{self.base_url}session"

    @property
    def vectorstore_url(self):
        return f"{self.base_url}vectorstores"

    @property
    def patterns_url(self):
        return f"{self.base_url}patterns"

class _Authenticate:
    """ Parent class to either grant or revoke access on the vector store. """

    def __init__(self, action, vs):
        """
        DESCRIPTION:
            Method to initialize the _Authenticate class.

        PARAMETERS:
            action:
                Required Arguments.
                Specifies the action to be performed (grant/revoke).
                Type: str

            vs:
                Required Arguments.
                Specifies the vector store object.
                Type: VectorStore
        
        RETURNS:
            None

        RAISES:
            None

        EXAMPLES:
            >>> _Authenticate(action="GRANT", vs=vs)
        """
        self.action = action
        self.vs = vs
        self.__set_user_permissions_url = "{0}permissions/{1}?user_name={2}&action={3}&permission={4}&log_level={5}"
        # Avoid circular import
        from teradatagenai.vector_store import VSManager
        self._session_header = VSManager._generate_session_id()
        self.__base_url = VectorStoreURLs().base_url

    def _submit_permission_request(self, username, permission):
        """
        DESCRIPTION:
            Internal function to submit the grant/revoke permission request to the vector store.

        PARAMETERS:
            username:
                Required Arguments.
                Specifies the name of the user.
                Type: str
            
            permission:
                Required Arguments.
                Specifies the type of permission to be provided.
                Type: str

        RETURNS:
            HTTP response

        RAISES:
            TeradataMLException

        EXAMPLES:
            >>> _Authenticate._submit_permission_request(username="test_user", permission=Permission.ADMIN.value)
        """
        # Validate the username
        arg_info_matrix = []
        arg_info_matrix.append(["username", username, False, (str), True])
        _Validators._validate_function_arguments(arg_info_matrix)

        # HTTP request to grant/revoke USER/ADMIN access to the user
        response = UtilFuncs._http_request(self.__set_user_permissions_url.format(
                                                                                  self.__base_url,
                                                                                  self.vs.name,
                                                                                  username,
                                                                                  self.action,
                                                                                  permission,
                                                                                  self.vs._log),
                                            HTTPRequest.PUT,
                                            headers=self._session_header['vs_header'],
                                            cookies={'session_id': self._session_header['vs_session_id']})
        # Return the response
        return response

    def admin(self, username):
        """
        DESCRIPTION:
            Internal function to provide admin permissions of the
            vector store to the user.

        PARAMETERS:
            username:
                Required Arguments.
                Specifies the name of the user.
                Type: str

        RETURNS:
            None

        RAISES:
            TeradataMLException

        EXAMPLES:
            >>> _Authenticate.admin(username="test_user")
        """
        # Submit the grant/revoke ADMIN permission request to the vector store for the user
        response = self._submit_permission_request(username, Permission.ADMIN.value)
        # Process the response
        self.vs._process_vs_response(self.action, response)

    def user(self, username):
        """
        DESCRIPTION:
            Internal function to provide user permissions to the vector store.

        PARAMETERS:
            username:
                Required Arguments.
                Specifies the name of the user.
                Type: str

        RETURNS:
            None

        RAISES:
            TeradataMLException

        EXAMPLES:
            >>> _Authenticate.user(username="test_user")
        """
        # Submit the grant/revoke USER permission request to the vector store for the user
        response = self._submit_permission_request(username, Permission.USER.value)
        # Process the response
        self.vs._process_vs_response(self.action, response)

class _Grant(_Authenticate):
    """ Class to grant access to the vector store."""
    def __init__(self, vs):
        super().__init__(Action.GRANT.value, vs)

class _Revoke(_Authenticate):
    """ Class to revoke access to the vector store."""
    def __init__(self, vs):
        super().__init__(Action.REVOKE.value, vs)

# Dict to map the python variable names of vs_parameters to REST variable names.
VSParameters = {
    "description": "description",
    "embeddings_model": "embeddings_model",
    "embeddings_dims": "embeddings_dims",
    "metric": "metric",
    "search_algorithm": "search_algorithm",
    "top_k": "top_k",
    "initial_centroids_method": "initial_centroids_method",
    "train_numcluster": "train_numcluster",
    "max_iternum": "max_iternum",
    "stop_threshold": "stop_threshold",
    "seed": "seed",
    "num_init": "num_init",
    "search_threshold": "search_threshold",
    "search_numcluster": "search_numcluster",
    "prompt": "prompt",
    "chat_completion_model": "chat_completion_model",
    "ef_search": "ef_search",
    "num_layer": "num_layer",
    "ef_construction": "ef_construction",
    "num_connpernode": "num_connPerNode",
    "maxnum_connpernode": "maxNum_connPerNode",
    "apply_heuristics": "apply_heuristics",
    "rerank_weight": "rerank_weight",
    "relevance_top_k": "relevance_top_k",
    "relevance_search_threshold": "relevance_search_threshold",
    "time_zone": "time_zone",
    "ignore_embedding_errors": "ignore_embedding_errors",
    "chat_completion_max_tokens": "chat_completion_max_tokens",
    "completions_base_url": "base_url_completions",
    "embeddings_base_url": "base_url_embeddings",
    "ingest_host": "doc_ingest_host",
    "ingest_port": "doc_ingest_port",
    #------------------ Oct ------------------
    "num_nodes_per_graph": "num_NodesPerGraph",
    "content_safety_base_url": "base_url_content_safety",
    "topic_control_base_url": "base_url_topic_control",
    "jailbreak_detection_base_url": "base_url_jailbreak_detection",
    "vlm_base_url": "base_url_vlm",
    "content_safety_model": "content_safety_model",
    "topic_control_model": "topic_control_model",
    "vlm_model": "vlm_model",
    "guardrails": "guardrails",
    "ranking_base_url": "base_url_ranking",
    "ranking_model": "ranking_model",
    "onnx_model_table": "onnx_model_table",
    "onnx_tokenizer_table": "onnx_tokenizer_table",
    "onnx_model_id": "onnx_model_id",
    "onnx_tokenizer_id": "onnx_tokenizer_id",
    "onnx_model_column": "onnx_model_column",
    "onnx_tokenizer_column": "onnx_tokenizer_column",
    "onnx_model_id_column": "onnx_model_id_column",
    "onnx_tokenizer_id_column": "onnx_tokenizer_id_column",
    "embedding_datatype": "embedding_datatype",
    "use_simd": "use_simd",
    "maximal_marginal_relevance": "maximal_marginal_relevance",
    "lambda_multiplier": "lambda_multiplier",
    "new_vs_name": "new_vs_name",
}

# Dict to map the python variable names of vs_index to REST variable names.
VSIndex = {
    "target_database": "target_database",
    "object_names": "object_names",
    "key_columns": "key_columns",
    "data_columns": "data_columns",
    "vector_column": "vector_column",
    "chunk_size": "chunk_size",
    "optimized_chunking": "optimized_chunking",
    "is_embedded": "is_embedded",
    "is_normalized": "is_normalized",
    "header_height": "header_height",
    "footer_height": "footer_height",
    "include_objects": "include_objects",
    "exclude_objects": "exclude_objects",
    "include_patterns": "include_patterns",
    "exclude_patterns": "exclude_patterns",
    "sample_size": "sample_size",
    "alter_operation": "alter_operation",
    "update_style": "update_style",
    "nv_ingestor": "nv_ingestor",
    "display_metadata": "display_metadata",
    "extract_text": "extract_text",
    "extract_images": "extract_images",
    "extract_tables": "extract_tables",
    "extract_method": "extract_method",
    "tokenizer": "tokenizer",
    "extract_infographics": "extract_infographics",
    "hf_access_token": "hf_access_token", 
    #------------------ Oct ------------------
    "metadata_columns": "metadata_columns",
    "metadata_descriptions": "metadata_descriptions",
    "chunk_overlap": "chunk_overlap",
    "extract_metadata_json": "extract_metadata_json",
    "extract_caption": "extract_caption",
    "overwrite_object": "overwrite_object",
    "metadata_operation": "metadata_operation",
}

# Similarity Search BY Vector Parameters by Drop Version
AUGUST_DROP_SIMILARITY_PARAMS = {
    "data": "input_table",
    "column": "input_query_column",
    "question": "question_vector"
}

# August drop URL pattern (question in URL)
AUGUST_DROP_SIMILARITY_SEARCH_URL = '{0}/similarity-search?question={1}&log_level={2}'

OCTOBER_DROP_SIMILARITY_PARAMS = {
    "data": "input_table",
    "column": "input_vector_column",
    "question": "question_vector"
}

# October drop URL pattern (question in body)
OCTOBER_DROP_SIMILARITY_SEARCH_URL = '{0}/similarity-search?log_level={1}'

# Ask Method Parameters - maps ask method parameters to API parameters
ASK_PARAMS = {
    "data": "input_table",
    "column": "input_query_column", 
    "vector_column": "input_vector_column"
}

# Mapping from client batch parameter names to backend parameter names
BATCH_PARAM_MAPPING = {
    "batch_data": "batch_input_table",
    "batch_id_column": "batch_input_id_column", 
    "batch_query_column": "batch_input_query_column",
    "batch_vector_column": "batch_input_vector_column"
}

# System parameters that should be excluded from search parameter passing
SYSTEM_PARAMS = ['return_type']

# Similarity search specific parameters for both similarity_search and similarity_search_by_vector methods
SIMILARITY_SEARCH_PARAMS = {
"top_k": {
    "argument_name": "top_k",
    "required": "Optional Argument",
    "description": "Specifies the number of similarity matches to be generated.",
    "notes": "",
    "default_values": "10",
    "permitted_values": "[1 - 1024]",
    "types": "int",
},

"search_threshold": {
    "argument_name": "search_threshold",
    "required": "Optional Argument", 
    "description": """Threshold value to consider matching tables/views while searching. 
                      A higher threshold value limits responses to the top matches only.""",
    "notes": """Only applicable when "search_algorithm" is 'VECTOR_DISTANCE' AND 'KMEANS'.""",
    "default_values": "",
    "permitted_values": "",
    "types": "float",
},

"search_numcluster": {
    "argument_name": "search_numcluster",
    "required": "Optional Argument",
    "description": """Number of clusters or fraction of train_numcluster to be considered while searching.""",
    "notes": """Applicable when "search_algorithm" is 'KMEANS'.
               If you want to pass a fraction of train_numcluster to be used for searching, 
               the supported range is (0, 1.0].
               If you want to pass the exact number of clusters to be used for searching, 
               the supported range is [1, train_numcluster].""",
    "default_values": "",
    "permitted_values": "",
    "types": "int or float",
},

"ef_search": {
    "argument_name": "ef_search",
    "required": "Optional Argument",
    "description": "Specify the number of neighbors to consider during search in HNSW graph.",
    "notes": """Applicable when "search_algorithm" is 'HNSW'.""",
    "default_values": "",
    "permitted_values": "[1 - 1024]",
    "types": "int",
},

"filter": {
    "argument_name": "filter",
    "required": "Optional Argument",
    "description": """Specifies the filter expression to be used for filtering the results. 
                      Supports logical operators (AND, OR, NOT), comparison operators 
                      (=, !=, <, <=, >, >=), and IN clauses with parentheses grouping.""",
    "notes": """Examples:
               * Simple condition: "age > 25"
               * Complex condition: "age >= 18 AND status = 'active'"
               * IN clause: "category IN ('A', 'B', 'C')"
               * Grouped conditions: "(age > 18 AND status = 'active') OR priority = 'high'"
               * String matching: "name != 'test' AND description LIKE '%important%'"
             """,
    "default_values": "",
    "permitted_values": "",
    "types": "str",
},

"filter_style": {
    "argument_name": "filter_style",
    "required": "Optional Argument",
    "description": "Specifies whether to apply filtering before or after the similarity_search.",
    "notes": "",
    "default_values": "PRE-FILTERING",
    "permitted_values": "PRE-FILTERING, POST-FILTERING",
    "types": "str",
},

"maximal_marginal_relevance": {
    "argument_name": "maximal_marginal_relevance",
    "required": "Optional Argument",
    "description": "Specifies whether to use Maximal Marginal Relevance (MMR) for retrieving documents.",
    "notes": "",
    "default_values": "",
    "permitted_values": "",
    "types": "bool",
},

"lambda_multiplier": {
    "argument_name": "lambda_multiplier",
    "required": "Optional Argument",
    "description": "Lambda multiplier to control the trade-off between relevance and diversity when selecting documents.",
    "notes": "",
    "default_values": "",
    "permitted_values": "0.0 to 1.0",
    "types": "float",
},

"batch_data": {
    "argument_name": "batch_data",
    "required": "Required for batch mode",
    "description": "Specifies the table name or teradataml DataFrame to be indexed for batch mode.",
    "notes": "Applicable only for AWS.",
    "default_values": "",
    "permitted_values": "",
    "types": "str, teradataml DataFrame",
},

"batch_id_column": {
    "argument_name": "batch_id_column",
    "required": "Required for batch mode",
    "description": "Specifies the ID column to be indexed for batch mode.",
    "notes": "Applicable only for AWS.",
    "default_values": "",
    "permitted_values": "",
    "types": "str",
},

"return_type": {
    "argument_name": "return_type",
    "required": "Optional Argument",
    "description": "Specifies the return type of similarity_search.",
    "notes": "",
    "default_values": "teradataml",
    "permitted_values": "teradataml, pandas, json",
    "types": "str",
},

}

FILE_BASED_VECTOR_STORE_PARAMS = {
"chunk_size": {
    "argument_name": "chunk_size",
    "required": "Optional Argument",
    "description": """Specifies the number of characters in each chunk to be used while
                      splitting the input file.""",
    "notes": """Applicable only for 'file-based' vector stores.""",
    "default_values": 512,
    "permitted_values": "",
    "types": "int",
},

"optimized_chunking": {
    "argument_name": "optimized_chunking",
    "required": "Optional Argument",
    "description": """Specifies whether an optimized splitting mechanism supplied by
                      Teradata should be used. The documents are parsed internally in an
                      intelligent fashion based on file structure and chunks are dynamically
                      created based on section layout.""",
    "notes": """* The "chunk_size" field is not applicable when
               "optimized_chunking" is set to True.
              * Applicable only for 'file-based' vector stores.""",
    "default_values": False,
    "permitted_values": "",
    "types": "bool",
},

"header_height": {
    "argument_name": "header_height",
    "required": "Optional Argument",
    "description": """Specifies the height (in points) of the header section of a PDF
                      document to be trimmed before processing the main content.
                      This is useful for removing unwanted header information
                      from each page of the PDF. Recommended value is 55.""",
    "notes": """* Applicable only for 'file-based' vector stores.""",
    "default_values": 0,
    "permitted_values": "",
    "types": "int",
},

"footer_height": {
    "argument_name": "footer_height",
    "required": "Optional Argument",
    "description": """Specifies the height (in points) of the footer section of a PDF
                      document to be trimmed before processing the main content.
                      This is useful for removing unwanted footer information from
                      each page of the PDF. Recommended value is 55.""",
    "notes": """* Applicable only for 'file-based' vector stores.""",
    "default_values": 0,
    "permitted_values": "",
    "types": "int",
},

"chunk_overlap": {
    "argument_name": "chunk_overlap",
    "required": "Optional Argument",
    "description": """Specifies the number of overlapping characters between two consecutive chunks
                      to be used during the splitting of the input file.""",
    "notes": "* Applicable only for 'file-based' vector stores.",
    "default_values": 150,
    "permitted_values": "",
    "types": "int",
},

"overwrite_object": {
    "argument_name": "overwrite_object",
    "required": "Optional Argument",
    "description": """Specifies whether to overwrite the existing object with
                      the same name in the database.""",
    "notes": "* Applicable only for 'file-based' vector stores.",
    "default_values": False,
    "permitted_values": "",
    "types": "bool",
},

"ingest_params": {
    "argument_name": "ingest_params",
    "required": "Optional Argument",
    "description": """Specifies the parameters to be used for document ingestion for NIM.""",
    "notes": """* Applicable only for NVIDIA NIM endpoint.
                * Applicable only for 'file-based' vector stores.
               * Refer to the IngestParams class for more details.""",
    "default_values": "",
    "permitted_values": "",
    "types": "IngestParams"
}
}

LANGCHAIN_PARAMS = {
    "embeddings_langchain": {
    "argument_name": "embedding",
    "required": "Required for NVIDIA NIM, Optional otherwise",
    "description": """Specifies the embeddings model to be used for generating the
                        embeddings.""",
    "notes": "",
    "default_values": """ For AWS: amazon.titan-embed-text-v2:0
                        For Azure: text-embedding-3-small""",
    "permitted_values": """For AWS:
                            * amazon.titan-embed-text-v1
                            * amazon.titan-embed-image-v1
                            * amazon.titan-embed-text-v2:0
                            For Azure:
                            * text-embedding-ada-002
                            * text-embedding-3-small
                            * text-embedding-3-large""",
    "types": "str, TeradataAI, LangChain Embeddings",
},

"chat_completion_model_lc": {
    "argument_name": "chat_completion_model",
    "required": "Required for NVIDIA NIM, Optional otherwise",
    "description": """Specifies the name of the chat completion model to be used for
                        generating text responses.""",
    "notes": "",
    "default_values": """ For AWS: anthropic.claude-3-haiku-20240307-v1:0
                        For Azure: gpt-35-turbo-16k""",
    "permitted_values": """*For AWS:
                                * anthropic.claude-3-haiku-20240307-v1:0
                                * anthropic.claude-instant-v1
                                * anthropic.claude-3-5-sonnet-20240620-v1:0
                            *For Azure:
                                * gpt-35-turbo-16k""",
    "types": "str, TeradataAI, LangChain BaseChatModel",
},
}

COMMON_PARAMS = {
"description": {
    "argument_name": "description",
    "required": "Optional Argument",
    "description": """Specifies the description of the vector store.""",
    "notes": "",
    "default_values": "",
    "permitted_values": "",
    "types": "str",
},

"target_db": {
    "argument_name": "target_database",
    "required": "Optional Argument",
    "description": """Specifies the database name where the vector store is created.""",
    "notes": """* If not specified, vector store is created in the database
                which is in use.""",
    "default_values": "",
    "permitted_values": "",
    "types": "str",
},

"vector_column": {
    "argument_name": "vector_column",
    "required": "Optional Argument",
    "description": """Specifies the name of the column to be used for storing
                      the embeddings.""",
    "notes": "",
    "default_values": "vector_index",
    "permitted_values": "",
    "types": "str",
},

"metadata_columns": {
    "argument_name": "metadata_columns",
    "required": "Optional Argument",
    "description": """Specifies the list of input column names to be used for metadata.
                      These columns just get accumulated in the vector store.""",
    "notes": "",
    "default_values": [],
    "permitted_values": "",
    "types": "list[str]",
},

"metadata_descriptions": {
    "argument_name": "metadata_descriptions",
    "required": "Optional Argument",
    "description": "Specifies the deescriptions of the metadata columns. One value for each metadata column.",
    "notes": "Applicable to all store types except metadata-based store type.",
    "default_values": [],
    "permitted_values": "",
    "types": "list[str]",
},

"use_simd": {
    "argument_name": "use_simd",
    "required": "Optional Argument",
    "description": """Specifies whether to use SIMD for faster processing.""",
    "notes": "",
    "default_values": False,
    "permitted_values": "",
    "types": "bool",
},

"embedding_datatype": {
    "argument_name": "embedding_datatype",
    "required": "Optional Argument",
    "description": """Specifies the data type of the embeddings to be used.""",
    "notes": "",
    "default_values": "VECTOR32",
    "permitted_values": "VECTOR32, VECTOR64",
    "types": "str",
},

"embeddings_tdgenai": {
    "argument_name": "embedding",
    "required": "Required for NVIDIA NIM, Optional otherwise",
    "description": """Specifies the embeddings model to be used for generating the
                        embeddings.""",
    "notes": "",
    "default_values": """ For AWS: amazon.titan-embed-text-v2:0
                        For Azure: text-embedding-3-small""",
    "permitted_values": """For AWS:
                            * amazon.titan-embed-text-v1
                            * amazon.titan-embed-image-v1
                            * amazon.titan-embed-text-v2:0
                            For Azure:
                            * text-embedding-ada-002
                            * text-embedding-3-small
                            * text-embedding-3-large
                            For NIM:
                            * Any hosted NVIDIA model for embedding generation""",
    "types": "str, TeradataAI",
},

"embeddings_dims": {
    "argument_name": "embeddings_dims",
    "required": "Required for NVIDIA NIM, Optional otherwise",
    "description": """Specifies the number of dimensions to be used for generating the embeddings.
                        The value depends on the "embeddings".""",
    "notes": "* Default dimesions is set to 1024 for embedding-based vector store.",
    "default_values": """ * For AWS:
                                * amazon.titan-embed-text-v1: 1536
                                * amazon.titan-embed-image-v1: 1024
                                * amazon.titan-embed-text-v2:0: 1024
                            * For Azure:
                                * text-embedding-ada-002: 1536
                                * text-embedding-3-small: 1536
                                * text-embedding-3-large: 3072""",
    "permitted_values": """*For AWS:
                                * amazon.titan-embed-text-v1: 1536
                                * amazon.titan-embed-image-v1: [256, 384, 1024]
                                * amazon.titan-embed-text-v2:0: [256, 512, 1024]
                            *For Azure:
                                * text-embedding-ada-002: 1536 only
                                * text-embedding-3-small: 1 <= dims <= 1536
                                * text-embedding-3-large: 1 <= dims <= 3072""",
    "types": "str",
},

"chat_completion_model_tdgenai": {
    "argument_name": "chat_completion_model",
    "required": "Required for NVIDIA NIM, Optional otherwise",
    "description": """Specifies the name of the chat completion model to be used for
                        generating text responses.""",
    "notes": "",
    "default_values": """ For AWS: anthropic.claude-3-haiku-20240307-v1:0
                        For Azure: gpt-35-turbo-16k""",
    "permitted_values": """*For AWS:
                                * anthropic.claude-3-haiku-20240307-v1:0
                                * anthropic.claude-instant-v1
                                * anthropic.claude-3-5-sonnet-20240620-v1:0
                            *For Azure:
                                * gpt-35-turbo-16k
                            *For NIM:
                                * Any hosted chat completion model""",
    "types": "str, TeradataAI",
},
"chat_completion_max_tokens": {
    "argument_name": "chat_completion_max_tokens",
    "required": "Required for NVIDIA NIM, Optional otherwise",
    "description": """Specifies the maximum number of tokens to be generated by the
                      "chat_completion_model".""",
    "notes": "",
    "default_values": 16384,
    "permitted_values": "[1, 16384]",
    "types": "int",

},
"model_urls": {
    "argument_name": "model_urls",
    "required": "Optional Argument",
    "description": """Specifies the URL and models to be used for embedding, chat completion
                        and guardrails.""",
    "notes": "* Refer to the ModelUrlParams class for more details.",
    "default_values": "",
    "permitted_values": "",
    "types": "ModelUrlParams"
},
}


UPDATE_PARAMS ={
"update_style": {
    "argument_name": "update_style",
    "required": "Optional Argument",
    "description": """Specifies the style to be used for alter operation of the data
                        from the vector store when "search_algorithm" is KMEANS/HNSW.""",
    "notes": "",
    "default_values": "MINOR",
    "permitted_values": "MINOR, MAJOR",
    "types": "str",
},
"metadata_operation": {
    "argument_name": "metadata_operation",
    "required": "Optional Argument",
    "description": """Specifies the operation to be performed on metadata columns
                        during update.
                        - ADD -  add new metadata columns
                        - DELETE - remove existing metadata columns
                        - MODIFY - change the description of the existing metadata columns
                        """,
    "notes": "* Applicable to all store types except the METADATA-BASED store type.",
    "default_values": "ADD",
    "permitted_values": "ADD, DELETE, MODIFY",
    "types": "str",
}
}

CREATE_UPDATE_COMMON_PARAMS = {
"description": {
    "argument_name": "description",
    "required": "Optional Argument",
    "description": """Specifies the description of the vector store.""",
    "notes": "",
    "default_values": "",
    "permitted_values": "",
    "types": "str",
},

"target_database": {
    "argument_name": "target_database",
    "required": "Optional Argument",
    "description": """Specifies the database name where the vector store is created.
                        When "document_files" is passed, it refers to the database where
                        the file content splits are stored.""",
    "notes": """If not specified, vector store is created in the database
                which is in use.""",
    "default_values": "",
    "permitted_values": "",
    "types": "str",
},

"data_columns": {
    "argument_name": "data_columns",
    "required": "Optional Argument",
    "description": """Specifies the name(s) of the data column(s) to be used
                        for embedding generation(vectorization).""",
    "notes": """* When multiple data columns are specified, data is unpivoted
                    to get a new key column "AttributeName" and a single data column
                    "AttributeValue".
                * When "document_files" is specified, specifies the column name 
                    where the content splits to be stored.""",
    "default_values": """content/embedding-based: []
                        file-based: ['file-splits']""",
    "permitted_values": "",
    "types": "str, list of str",
},

"key_columns": {
    "argument_name": "key_columns",
    "required": "Optional Argument",
    "description": """Specifies the name(s) of the key column(s) to be used for indexing.""",
    "notes": """* Not supported, when "document_files" is used.
                * In case of multiple input files, a key_column containing
                    the file names is generated.""",
    "default_values": """content/embedding-based: ['TD_ID']
                        file-based: ['TD_ID', 'TD_FILENAME']""",
    "permitted_values": "",
    "types": "str, list of str",
},

"metadata_columns": {
    "argument_name": "metadata_columns",
    "required": "Optional Argument",
    "description": "List of input column names to be used for metadata. These columns just get accumulated in the vector store.",
    "notes": """* Applicable to all store types except metadata-based store type.
                * When "document_files" is used, a metadata column containing
                    the source file name is generated by default.""",
    "default_values": [],
    "permitted_values": "",
    "types": "list[str]",
},

"metadata_descriptions": {
    "argument_name": "metadata_descriptions",
    "required": "Optional Argument",
    "description": "Descriptions of the metadata columns. One value for each metadata column.",
    "notes": "Applicable to all store types except metadata-based store type.",
    "default_values": [],
    "permitted_values": "",
    "types": "list[str]",
},

"document_files": {
    "argument_name": "document_files",
    "required": "Optional Argument",
    "description": """Specifies the input dataset in document files format.
                        It can be used to specify input documents in file format.
                        A directory path or wildcard pattern can also be specified
                        The files are processed internally, converted to chunks and stored
                        into a database table.""",
    "notes": """* Only PDF format is currently supported.
                * Multiple document files can be supplied.
                * Fully qualified file name should be specified.""",
    "examples": """    Example 1 : Multiple files specified within a list
    >>> document_files=['file1.pdf','file2.pdf']

    Example 2 : Path to the directory containing pdf files 
    >>> document_files = "/path/to/pdfs"

    Example 3 : Path to directory containing pdf files as a wildcard string
    >>> document_files = "/path/to/pdfs/*.pdf"

    Example 4 : Path to directory containing pdf files and subdirectory of pdf files
    >>> document_files = "/path/to/pdfs/**/*.pdf""",
    
    "default_values": "",
    "permitted_values": "",
    "types": "str, list",
},

"vector_column": {
    "argument_name": "vector_column",
    "required": "Optional Argument",
    "description": """Specifies the name of the column to be used for storing
                        the embeddings.""",
    "notes": "",
    "default_values": "vector_index",
    "permitted_values": "",
    "types": "str",
},
"embedding_data_columns": {
    "argument_name": "embedding_data_columns",
    "required": "Required for 'embedding-based' vector stores, Optional otherwise",
    "description": """Specifies the name(s) of the column(s) containing the
                        pre-computed embeddings.""",
    "notes": """* Applicable only for 'embedding-based' vector store.
                * Currently only one column is supported that will be referenced as text""",
    "default_values": "",
    "permitted_values": "",
    "types": "str, list of str",
},
"is_embedded": {
    "argument_name": "is_embedded",
    "required": "Required for 'embedding-based' vector stores, Optional otherwise",
    "description": """Specifies whether the input contains the embedded data.""",
    "notes": """Applicable only for 'embedding-based' vector store.""",
    "default_values": False,
    "permitted_values": "",
    "types": "bool",
},

"is_normalized": {
    "argument_name": "is_normalized",
    "required": "Optional Argument",
    "description": """Specifies whether the input contains normalized embedding.""",
    "notes": """Applicable only for 'embedding-based' vector store.""",
    "default_values": False,
    "permitted_values": "",
    "types": "bool",
},

"include_objects": {
    "argument_name": "include_objects",
    "required": "Optional Argument",
    "description": """Specifies the list of tables and views included
                        in the metadata-based vector store.""",
    "notes": """Applicable only for 'metadata-based' vector store.""",
    "default_values": "",
    "permitted_values": "",
    "types": "str, list of str, DataFrame",
},

"exclude_objects": {
    "argument_name": "exclude_objects",
    "required": "Optional Argument",
    "description": """Specifies the list of tables and views excluded from
                        the metadata-based vector store.""",
    "notes": """Applicable only for 'metadata-based' vector store.""",
    "default_values": "",
    "permitted_values": "",
    "types": "str, list of str, DataFrame",
},

"include_patterns": {
    "argument_name": "include_patterns",
    "required": "Optional Argument",
    "description": """Specifies the list of patterns to be included in the metadata-based vector store.""",
    "notes": """Applicable only for 'metadata-based' vector store.""",
    "default_values": "",
    "permitted_values": "",
    "types": "VSPattern, list of VSPattern",
},

"exclude_patterns": {
    "argument_name": "exclude_patterns",
    "required": "Optional Argument",
    "description": """Specifies the list of patterns to be excluded from the metadata-based vector store.""",
    "notes": """Applicable only for 'metadata-based' vector store.""",
    "default_values": "",
    "permitted_values": "",
    "types": "VSPattern, list of VSPattern",
},

"sample_size": {
    "argument_name": "sample_size",
    "required": "Optional Argument",
    "description": """Specifies the number of rows to sample from tables and views
                        for the metadata-based vector store embeddings.""",
    "notes": """Applicable only for 'metadata-based' vector store.""",
    "default_values": 20,
    "permitted_values": "",
    "types": "int",
},

"prompt": {
    "argument_name": "prompt",
    "required": "Optional Argument",
    "description": """Specifies the prompt to be used by language model
                        to generate responses using top matches.""",
    "notes": "",
    "default_values": "",
    "permitted_values": "",
    "types": "str",
},
"use_simd": {
    "argument_name": "use_simd",
    "required": "Optional Argument",
    "description": """Specifies whether to use SIMD for faster processing.""",
    "notes": "",
    "default_values": False,
    "permitted_values": "",
    "types": "bool",
}
}

MODEL_URL_PARAMS = {
"embeddings_tdgenai": {
    "argument_name": "embedding",
    "required": "Required for NVIDIA NIM, Optional otherwise",
    "description": """Specifies the embeddings model to be used for generating the
                        embeddings.""",
    "notes": "",
    "default_values": """ For AWS: amazon.titan-embed-text-v2:0
                        For Azure: text-embedding-3-small""",
    "permitted_values": """For AWS:
                            * amazon.titan-embed-text-v1
                            * amazon.titan-embed-image-v1
                            * amazon.titan-embed-text-v2:0
                            For Azure:
                            * text-embedding-ada-002
                            * text-embedding-3-small
                            * text-embedding-3-large
                            For NIM:
                            * Any hosted NVIDIA model for embedding generation""",   
    "types": "str, TeradataAI",
},

"chat_completion_model_tdgenai": {
    "argument_name": "chat_completion_model",
    "required": "Required for NVIDIA NIM, Optional otherwise",
    "description": """Specifies the name of the chat completion model to be used for
                        generating text responses.""",
    "notes": "",
    "default_values": """ For AWS: anthropic.claude-3-haiku-20240307-v1:0
                        For Azure: gpt-35-turbo-16k""",
    "permitted_values": """*For AWS:
                                * anthropic.claude-3-haiku-20240307-v1:0
                                * anthropic.claude-instant-v1
                                * anthropic.claude-3-5-sonnet-20240620-v1:0
                            *For Azure:
                                * gpt-35-turbo-16k
                            * For NIM:
                                * Any hosted chat completion model""",
    "types": "str, TeradataAI",
},

"embeddings_base_url": {
    "argument_name": "embeddings_base_url",
    "required": "Required for NVIDIA NIM, Optional otherwise",
    "description": """Specifies the base URL for the service to be used for generating embeddings.""",
    "notes": """* Applicable only while using NVIDIA NIM endpoints.""",
    "default_values": "",
    "permitted_values": "",
    "types": "str",
},

"completions_base_url": {
    "argument_name": "completions_base_url",
    "required": "Optional Argument",
    "description": """Specifies the base URL for the service to be used for generating completions.""",
    "notes": """* Applicable only while using NVIDIA NIM endpoints.""",
    "default_values": "",
    "permitted_values": "",
    "types": "str",
},

"content_safety_base_url": {
    "argument_name": "content_safety_base_url",
    "required": "Optional Argument",
    "description": """Specifies the base URL for Guardrails model, which ensures safe outputs from LLM.""",
    "notes": """* Applicable only while using NVIDIA NIM endpoints.""",
    "default_values": "",
    "permitted_values": "",
    "types": "str",
},

"topic_control_base_url": {
    "argument_name": "topic_control_base_url",
    "required": "Optional Argument",
    "description": """Specifies the base URL for Guardrails model, which ensures topic control.""",
    "notes": """* Applicable only while using NVIDIA NIM endpoints.""",
    "default_values": "",
    "permitted_values": "",
    "types": "str",
},

"jailbreak_detection_base_url": {
    "argument_name": "jailbreak_detection_base_url",
    "required": "Optional Argument",
    "description": """Specifies the base URL for Guardrails model, which ensures jailbreak detection.""",
    "notes": """* Applicable only while using NVIDIA NIM endpoints.""",
    "default_values": "",
    "permitted_values": "",
    "types": "str",
},

"content_safety_model": {
    "argument_name": "content_safety_model",
    "required": "Optional Argument",
    "description": """Specifies the guardrails model for content safety, which ensures safe outputs from LLM.""",
    "notes": """* Applicable only while using NVIDIA NIM endpoints.""",
    "default_values": "",
    "permitted_values": "",
    "types": "str",
},

"topic_control_model": {
    "argument_name": "topic_control_model",
    "required": "Optional Argument",
    "description": """Specifies the guardrails model for topic control.""",
    "notes": """* Applicable only while using NVIDIA NIM endpoints.""",
    "default_values": "",
    "permitted_values": "",
    "types": "str",
},

"guardrails": {
    "argument_name": "guardrails",
    "required": "Optional Argument",
    "description": """Specifies what kind of Guardrails to apply.""",
    "notes": """* Applicable only while using NVIDIA NIM endpoints.""",
    "default_values": "[]",
    "permitted_values": "content_safety, topic_control, jailbreak_detection",
    "types": "list[str]",
},

"ranking_base_url": {
    "argument_name": "ranking_base_url",
    "required": "Optional Argument",
    "description": """Specifies the base URL for the service to be used for the reranker model.""",
    "notes": """* Applicable only while using NVIDIA NIM endpoints.""",
    "default_values": "",
    "permitted_values": "",
    "types": "str",
},
"ranking_model": {
    "argument_name": "ranking_model",
    "required": "Optional Argument",
    "description": """Specifies the model to be used for reranking the search results.""",
    "notes": """* Applicable only while using NVIDIA NIM endpoints.""",
    "default_values": "",
    "permitted_values": "",
    "types": "str",
},
}

INGEST_PARAMS = {
"nv_ingestor": {
    "argument_name": "nv_ingestor",
    "required": "Optional Argument",
    "description": """Specifies whether to use NVIDIA NV-Ingest for processing the
                      document files.""",
    "notes": """* Applicable only while using NVIDIA NIM endpoints.
               * Applicable only for 'file-based' vector stores.""",
    "default_values": False,
    "permitted_values": "",
    "types": "bool",
},

"ingest_host": {
    "argument_name": "ingest_host",
    "required": "Required for NVIDIA NIM, Optional otherwise",
    "description": """Specifies the HTTP host for the service to be used for document parsing.""",
    "notes": """* Applicable only while using NVIDIA NIM endpoints.""",
    "default_values": "",
    "permitted_values": "",
    "types": "str",
},

"ingest_port": {
    "argument_name": "ingest_port",
    "required": "Optional Argument",
    "description": """Specifies the HTTP port for the service to be used for document parsing.""",
    "notes": """* Applicable only while using NVIDIA NIM endpoints.""",
    "default_values": 7670,
    "permitted_values": "",
    "types": "int",
},

"display_metadata": {
    "argument_name": "display_metadata",
    "required": "Optional Argument",
    "description": """Specifies whether to display metadata describing objects extracted
                      from document files when using NVIDIA NV-Ingest.""",
    "notes": """* Applicable only for 'file-based' vector stores.
                * Applicable only while using NVIDIA NIM endpoints and
                  when "nv_ingestor" is set to True.""",
    "default_values": False,
    "permitted_values": "",
    "types": "bool",
},

"extract_text": {
    "argument_name": "extract_text",
    "required": "Optional Argument",
    "description": """Specifies whether to extract text from the document files when
                      using NVIDIA NV-Ingest.""",
    "notes": """* Applicable only for 'file-based' vector stores.
                * Applicable only while using NVIDIA NIM endpoints and
                  when "nv_ingestor" is set to True.""",
    "default_values": True,
    "permitted_values": "",
    "types": "bool",
},

"extract_images": {
    "argument_name": "extract_images",
    "required": "Optional Argument",
    "description": """Specifies whether to extract images from the document files when
                      using NVIDIA NV-Ingest.""",
    "notes": """* Applicable only for 'file-based' vector stores.
                * Applicable only while using NVIDIA NIM endpoints and
                  when "nv_ingestor" is set to True.""",
    "default_values": True,
    "permitted_values": "",
    "types": "bool",
},

"extract_tables": {
    "argument_name": "extract_tables",
    "required": "Optional Argument",
    "description": """Specifies whether to extract tables from the document files when
                      using NVIDIA NV-Ingest.""",
    "notes": """* Applicable only for 'file-based' vector stores.
                * Applicable only while using NVIDIA NIM endpoints and
                    when "nv_ingestor" is set to True.""",
    "default_values": True,
    "permitted_values": "",
    "types": "bool",
},

"extract_infographics": {
    "argument_name": "extract_infographics",
    "required": "Required for NVIDIA NIM, Optional otherwise",
    "description": """Specifies whether to extract infographics from
                      document files.""",
    "notes": """* Applicable only for 'file-based' vector stores.
                * Applicable only while using NVIDIA NIM endpoints and
                  when "nv_ingestor" is set to True.""",
    "default_values": False,
    "permitted_values": "",
    "types": "bool",
},

"extract_method": {
    "argument_name": "extract_method",
    "required": "Required for NVIDIA NIM, Optional otherwise",
    "description": """Specifies the method to be used for extracting text from
                      the document files.""",
    "notes": """* Applicable only for 'file-based' vector stores.
                * Applicable only while using NVIDIA NIM endpoints and
                  when "nv_ingestor" is set to True.""",
    "default_values": "pdfium",
    "permitted_values": "pdfium, nemoretriever_parse",
    "types": "str",
},

"extract_metadata_json": {
    "argument_name": "extract_metadata_json",
    "required": "Optional Argument",
    "description": """Specifies whether to extract metadata in JSON format and store it in
                      the metadata_json column when using NVIDIA NV-Ingest.""",
    "notes": """* Applicable only for 'file-based' vector stores.
                * Applicable only while using NVIDIA NIM endpoints and
                  when "nv_ingestor" is set to True.""",
    "default_values": False,
    "permitted_values": "",
    "types": "bool",
},

"extract_caption": {
    "argument_name": "extract_caption",
    "required": "Optional Argument",
    "description": """Specifies whether to extract captions for images and tables from
                      the document files when using NVIDIA NV-Ingest.""",
    "notes": """* Applicable only for 'file-based' vector stores.
                * Applicable only while using NVIDIA NIM endpoints and
                  when "nv_ingestor" is set to True.""",
    "default_values": False,
    "permitted_values": "",
    "types": "bool",
},

"tokenizer": {
    "argument_name": "tokenizer",
    "required": "Optional Argument",
    "description": """Specifies the tokenizer to be used for splitting the text into chunks.""",
    "notes": """* Applicable only when "nv_ingestor" is set to True
               and "document_files" is supplied.
              * Applicable only while using NVIDIA NIM endpoints.""",
    "default_values": "meta-llama/Llama-3.2-1B",
    "permitted_values": "",
    "types": "str",
},

"overwrite_object": {
    "argument_name": "overwrite_object",
    "required": "Optional Argument",
    "description": """Specifies whether to overwrite the existing object with
                      the same name in the database.""",
    "notes": "* Applicable only for 'file-based' vector stores.",
    "default_values": False,
    "permitted_values": "",
    "types": "bool",
},

"vlm_base_url": {
    "argument_name": "vlm_base_url",
    "required": "Optional Argument",
    "description": """Specifies the base URL for Vision Language Model when extract_caption from images is enabled.""",
    "notes": """* Applicable only for 'file-based' vector stores.
                * Applicable only while using NVIDIA NIM endpoints.
                * Applicable only when "extract_caption" is set to True.""",
    "default_values": "",
    "permitted_values": "",
    "types": "str",
},

"vlm_model": {
    "argument_name": "vlm_model",
    "required": "Optional Argument",
    "description": """Specifies the Vision Language Model to be used when extract_caption from images is enabled.""",
    "notes": """* Applicable only for 'file-based' vector stores.
                * Applicable only while using NVIDIA NIM endpoints.
                * Applicable only when "extract_caption" is set to True.""",
    "default_values": "",
    "permitted_values": "",
    "types": "str",
},
}

COMMON_SEARCH_PARAMS = {
"metric": {
    "argument_name": "metric",
    "required": "Optional Argument",
    "description": """Specifies the metric to be used for calculating the distance
                      between the vectors.""",
    "notes": "",
    "default_values": "COSINE",
    "permitted_values": "EUCLIDEAN, COSINE, DOTPRODUCT",
    "types": "str",
},

"search_algorithm": {
    "argument_name": "search_algorithm",
    "required": "Optional Argument",
    "description": """Specifies the algorithm to be used for searching the
                      tables and views relevant to the question.""",
    "notes": "",
    "default_values": "VECTORDISTANCE",
    "permitted_values": "VECTORDISTANCE, KMEANS, HNSW",
    "types": "str",
},

"top_k": {
    "argument_name": "top_k",
    "required": "Optional Argument",
    "description": """Specifies the number of top clusters to be considered while searching.""",
    "notes": "",
    "default_values": 10,
    "permitted_values": "[1, 1024]",
    "types": "int",
},

"rerank_weight": {
    "argument_name": "rerank_weight",
    "required": "Optional Argument",
    "description": """Specifies the weight to be used for reranking the search results.
                      Applicable range is 0.0 to 1.0.""",
    "notes": "",
    "default_values": 0.2,
    "permitted_values": "",
    "types": "float",
},

"relevance_top_k": {
    "argument_name": "relevance_top_k",
    "required": "Optional Argument",
    "description": """Specifies the number of top similarity matches to be considered for reranking.
                      Applicable range is 1 to 1024.""",
    "notes": "",
    "default_values": "max(top_k*2, 60)",
    "permitted_values": "[1, 1024]",
    "types": "int",
},

"relevance_search_threshold": {
    "argument_name": "relevance_search_threshold",
    "required": "Optional Argument",
    "description": """Specifies the threshold value to consider matching tables/views while reranking.
                      A higher threshold value limits responses to the top matches only.""",
    "notes": "",
    "default_values": "",
    "permitted_values": "",
    "types": "float",
},
"maximal_marginal_relevance": {
    "argument_name": "maximal_marginal_relevance",
    "required": "Optional Argument",
    "description": "Specifies whether to use Maximal Marginal Relevance (MMR) for retrieving documents.",
    "notes": "",
    "default_values": "",
    "permitted_values": "",
    "types": "bool",
},
"lambda_multiplier": {
    "argument_name": "lambda_multiplier",
    "required": "Optional Argument",
    "description": "Specifies lambda multiplier to control the trade-off between relevance and diversity when selecting documents.",
    "notes": "",
    "default_values": "",
    "permitted_values": "0.0 to 1.0",
    "types": "float",
}
}

HNSW_SEARCH_PARAMS = {
"ef_search": {
    "argument_name": "ef_search",
    "required": "Optional Argument",
    "description": """Specifies the number of neighbors to be considered during search
                      in HNSW graph.""",
    "notes": """Applicable when "search_algorithm" is 'HNSW'.""",
    "default_values": 32,
    "permitted_values": "[1, 1024]",
    "types": "int",
},

"num_layer": {
    "argument_name": "num_layer",
    "required": "Optional Argument",
    "description": """Specifies the maximum number of layers for the HNSW graph.""",
    "notes": """Applicable when "search_algorithm" is 'HNSW'.""",
    "default_values": "",
    "permitted_values": "[1, 1024]",
    "types": "int",
},

"ef_construction": {
    "argument_name": "ef_construction",
    "required": "Optional Argument",
    "description": """Specifies the number of neighbors to be considered during
                      construction of the HNSW graph.""",
    "notes": """Applicable when "search_algorithm" is 'HNSW'.""",
    "default_values": 32,
    "permitted_values": "[1, 1024]",
    "types": "int",
},

"num_connpernode": {
    "argument_name": "num_connpernode",
    "required": "Optional Argument",
    "description": """Specifies the number of connections per node in the HNSW graph
                      during construction.""",
    "notes": """Applicable when "search_algorithm" is 'HNSW'.""",
    "default_values": 32,
    "permitted_values": "[1, 1024]",
    "types": "int",
},

"maxnum_connpernode": {
    "argument_name": "maxnum_connpernode",
    "required": "Optional Argument",
    "description": """Specifies the maximum number of connections per node in the
                      HNSW graph during construction.""",
    "notes": """Applicable when "search_algorithm" is 'HNSW'.""",
    "default_values": 32,
    "permitted_values": "[1, 1024]",
    "types": "int",
},

"apply_heuristics": {
    "argument_name": "apply_heuristics",
    "required": "Optional Argument",
    "description": """Specifies whether to apply heuristics optimizations during construction
                      of the HNSW graph.""",
    "notes": """Applicable when "search_algorithm" is 'HNSW'.""",
    "default_values": True,
    "permitted_values": "",
    "types": "bool",
},

"num_nodes_per_graph": {
    "argument_name": "num_nodes_per_graph",
    "required": "Optional Argument",
    "description": """Specifies the number of nodes per graph in the HNSW construction.""",
    "notes": """Applicable when "search_algorithm" is 'HNSW'.""",
    "default_values": None,
    "permitted_values": "[1-2147483647]",
    "types": "int",
},
}

KMEANS_SEARCH_PARAMS = {
"initial_centroids_method": {
    "argument_name": "initial_centroids_method",
    "required": "Optional Argument",
    "description": """Specifies the algorithm to be used for initializing the
                      centroids.""",
    "notes": """Applicable when "search_algorithm" is 'KMEANS'.""",
    "default_values": "RANDOM",
    "permitted_values": "RANDOM, KMEANS++",
    "types": "str",
},

"train_numcluster": {
    "argument_name": "train_numcluster",
    "required": "Optional Argument",
    "description": """Specifies the number of clusters to be trained.""",
    "notes": """Applicable when "search_algorithm" is 'KMEANS'.""",
    "default_values": "",
    "permitted_values": "",
    "types": "int",
},

"max_iternum": {
    "argument_name": "max_iternum",
    "required": "Optional Argument",
    "description": """Specifies the maximum number of iterations to be run during
                      training.""",
    "notes": """Applicable when "search_algorithm" is 'KMEANS'.""",
    "default_values": 10,
    "permitted_values": "[1, 2147483647]",
    "types": "int",
},

"stop_threshold": {
    "argument_name": "stop_threshold",
    "required": "Optional Argument",
    "description": """Specifies the threshold value at which training should be
                      stopped.""",
    "notes": """Applicable when "search_algorithm" is 'KMEANS'.""",
    "default_values": 0.0395,
    "permitted_values": "",
    "types": "float",
},

"seed": {
    "argument_name": "seed",
    "required": "Optional Argument",
    "description": """Specifies the seed value to be used for random number
                      generation.""",
    "notes": """Applicable when "search_algorithm" is 'KMEANS'.""",
    "default_values": 0,
    "permitted_values": "[0, 2147483647]",
    "types": "int",
},

"num_init": {
    "argument_name": "num_init",
    "required": "Optional Argument",
    "description": """Specifies the number of times the k-means algorithm should
                      run with different initial centroid seeds.""",
    "notes": "",
    "default_values": 1,
    "permitted_values": "[1, 2147483647]",
    "types": "int",
},

"search_threshold": {
    "argument_name": "search_threshold",
    "required": "Optional Argument",
    "description": """Specifies the threshold value to consider for matching tables/views
                      while searching. A higher threshold value limits responses to the top matches only.""",
    "notes": """Applicable when "search_algorithm" is 'VECTORDISTANCE' and 'KMEANS'.""",
    "default_values": "",
    "permitted_values": "",
    "types": "float",
},

"search_numcluster": {
    "argument_name": "search_numcluster",
    "required": "Optional Argument",
    "description": """Specifies the number of clusters to be considered while
                      searching.""",
    "notes": """Applicable when "search_algorithm" is 'KMEANS'.""",
    "default_values": "",
    "permitted_values": "",
    "types": "int",
},
}

NV_INGEST_PARAMS = {
    "embeddings_dims": {
        "argument_name": "embeddings_dims",
        "required": "Required Argument",
        "description": """Specifies the number of dimensions to be used for generating the embeddings.
                          The value depends on the 'embeddings_model'.""",
        "notes": "",
        "default_values": "",
        "permitted_values": "",
        "types": "int",
    },
    "enable_text": {
        "argument_name": "enable_text",
        "required": "Optional Argument",
        "description": """Specifies whether to include text-type documents in the vector store.
                          When True, ensures all text type records are processed and included.""",
        "notes": "",
        "default_values": True,
        "permitted_values": "",
        "types": "bool",
    },
    "enable_charts": {
        "argument_name": "enable_charts",
        "required": "Optional Argument",
        "description": """Specifies whether to include chart-type structured documents.
                          When True, ensures all chart type records are processed and included.""",
        "notes": "",
        "default_values": True,
        "permitted_values": "",
        "types": "bool",
    },
    "enable_tables": {
        "argument_name": "enable_tables",
        "required": "Optional Argument",
        "description": """Specifies whether to include table-type structured documents.
                          When True, ensures all table type records are processed and included.""",
        "notes": "",
        "default_values": True,
        "permitted_values": "",
        "types": "bool",
    },
    "enable_images": {
        "argument_name": "enable_images",
        "required": "Optional Argument",
        "description": """Specifies whether to include image documents in the vector store.
                          When True, ensures all image type records (captions) are processed and included.""",
        "notes": "",
        "default_values": True,
        "permitted_values": "",
        "types": "bool",
    },
    "enable_infographics": {
        "argument_name": "enable_infographics",
        "required": "Optional Argument",
        "description": """Specifies whether to include infographic-type structured documents.
                          When True, ensures all infographic type records are processed and included.""",
        "notes": "",
        "default_values": True,
        "permitted_values": "",
        "types": "bool",
    },
    "enable_audio": {
        "argument_name": "enable_audio",
        "required": "Optional Argument",
        "description": """Specifies whether to include audio documents in the vector store.
                          When True, ensures all audio type records (transcripts) are processed and included.""",
        "notes": "",
        "default_values": True,
        "permitted_values": "",
        "types": "bool",
    }
}