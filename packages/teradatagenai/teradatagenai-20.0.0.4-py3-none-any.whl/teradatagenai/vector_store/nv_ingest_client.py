"""
Copyright (c) 2025 by Teradata Corporation. All rights reserved.
TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET

Primary Owner: aanchal.kavedia@teradata.com
Secondary Owner: Sushant.Mhambrey@Teradata.com
NVIDIA NV-Ingest Client utilities for Teradata Vector Store.

This module provides utilities for creating and managing vector store schemas
compatible with NVIDIA NV-Ingest processing pipeline.
"""

# Standard library imports
import copy, json
from typing import Any, Dict
import logging
import time
import pandas as pd

# teradataml library imports
from teradataml import copy_to_sql, DataFrame
from teradataml.common.utils import UtilFuncs
from ..common.utils import GenAIUtilFuncs
from teradataml.telemetry_utils.queryband import collect_queryband
from teradataml.utils.validators import _Validators


# Local application imports
from teradatagenai.vector_store.vector_store import VectorStore
from teradatagenai.common.constants import NVIngestSchemaColumns, COMMON_PARAMS, FILE_BASED_VECTOR_STORE_PARAMS,SIMILARITY_SEARCH_PARAMS,\
                                           MODEL_URL_PARAMS, INGEST_PARAMS, COMMON_SEARCH_PARAMS, KMEANS_SEARCH_PARAMS, HNSW_SEARCH_PARAMS,\
                                           NV_INGEST_PARAMS

from teradatagenai.common.exceptions import TeradataGenAIException
from teradatagenai.common.message_codes import MessageCodes as MessageCodesGenAI
from teradatagenai.common.messages import Messages as MessagesGenAI
from teradatagenai.utils.doc_decorator import docstring_handler

logger = logging.getLogger(__name__)

@collect_queryband(queryband="VS_NVIngest_create")
def create_nvingest_schema(name: str, recreate: bool = False, **kwargs: Any) -> Dict[str, Any]:
    """
    DESCRIPTION:
        Create a default schema for NVIDIA NV-Ingest compatible vector store.
        This function creates a schema structure that is compatible with NVIDIA NV-Ingest
        processing pipeline.
        The schema includes fields for embeddings and metadata that are specific to
        Teradata Vector Store implementation.
        The schema includes the following columns:
            * TDID: Integer column for unique document IDs.
            * TD_FILENAME: Unicode column for source filenames.
            * text: Unicode column for file content splits.
            * embeddings: Vector column for storing document embeddings.

    PARAMETERS:
        name:
            Required Argument.
            Specifies the name of the vector store/schema to create.
            Types: str

        recreate:
            Optional Argument.
            Specifies whether to recreate the schema if it already exists.
            If True, destroys existing vector store before creating new one.
            Default Value: False
            Types: bool

        **kwargs:
            Optional Argument.
            Specifies additional keyword arguments for schema configuration.
            Types: Any

    RETURNS:
        Dict[str, Any]: A dictionary containing the data type mapping for the schema
                       with column definitions for TDID, TD_FILENAME, text, and embeddings.

    RAISES:
        None

    EXAMPLES:
        >>> from teradatagenai.vector_store.nv_ingest_client import create_nvingest_schema
        
        # Example 1: Create a new schema with default settings
        >>> schema = create_nvingest_schema("my_vectorstore")
        >>> print(schema)
        {'TDID': INTEGER(), 'TD_FILENAME': VARCHAR(64000), 'text': VARCHAR(64000), 'embeddings': VECTOR()}
        
        # Example 2: Create schema without recreating existing vector store
        >>> schema = create_nvingest_schema("existing_vectorstore", recreate=False)
        
        # Example 3: Create schema with additional configuration
        >>> schema = create_nvingest_schema("custom_vectorstore", recreate=True, custom_param="value")
    """
    
    # Validations
    arg_info_matrix = []
    arg_info_matrix.append(["name", name, False, (str), True])
    arg_info_matrix.append(["recreate", recreate, True, (bool)])

    # Validate argument types.
    _Validators._validate_missing_required_arguments(arg_info_matrix)
    _Validators._validate_function_arguments(arg_info_matrix)

    # Get the standard schema mapping for NV-Ingest compatibility using the enum
    dtype_mapping = NVIngestSchemaColumns.get_dtype_mapping()
    
    from teradatagenai import VectorStore, VSManager
    vec_ins = VectorStore(name=name)
    vs_list = VSManager.list(return_type="json")
    if not recreate and vec_ins.exists:
        print("Vector Store already exists, it will be updated with new data.")
    else:
        if vec_ins.exists:
            # Destroy existing vector store if it exists and recreate is requested.
            vec_ins.destroy()

    return dtype_mapping

def verify_embedding(element):
    """
    DESCRIPTION:
        Verify if an element contains a valid embedding in its metadata.
        This function checks whether the provided element has a non-None embedding
        value in its metadata structure, which is required for vector operations.
        This function is typically used as a validation step before processing elements.
        Elements without embeddings are usually filtered out in the processing pipeline.

    PARAMETERS:
        element:
            Required Argument.
            Specifies the document element to check for embedding presence.
            Expected to be a dictionary with 'metadata' key containing 'embedding' field.
            Types: dict

    RETURNS:
        bool: True if the element contains a valid (non-None) embedding, False otherwise.

    RAISES:
        KeyError: If the element structure is invalid or missing required keys.

    EXAMPLES:
        >>> element_with_embedding = {
        ...     "metadata": {"embedding": [0.1, 0.2, 0.3]}
        ... }
        >>> verify_embedding(element_with_embedding)
        True
        
        >>> element_without_embedding = {
        ...     "metadata": {"embedding": None}
        ... }
        >>> verify_embedding(element_without_embedding)
        False
    """
    if element["metadata"]["embedding"] is not None:
        return True
    return False

def _pull_text(
    element,
    enable_text: bool,
    enable_charts: bool,
    enable_tables: bool,
    enable_images: bool,
    enable_infographics: bool,
    enable_audio: bool
):
    """
    DESCRIPTION:
        Extract text content from a document element based on document type and filter settings.
        This function intelligently extracts text from different document types (text, structured, image)
        while respecting the enabled filter flags. It also validates text length and embedding presence.
        Notes:
            - Text longer than 65535 characters is rejected with a warning. 
            - Elements without embeddings are automatically rejected.
            - Different document types require different metadata structures.
            - Logs debug messages for rejected elements.

    PARAMETERS:
        element:
            Required Argument.
            Specifies the document element containing metadata and content information.
            Expected to have 'document_type' and 'metadata' fields with appropriate structure.
            Types: dict

        enable_text:
            Required Argument.
            Specifies whether to extract text from text-type documents.
            Types: bool

        enable_charts:
            Required Argument.
            Specifies whether to extract text from chart-type structured documents.
            Types: bool

        enable_tables:
            Required Argument.
            Specifies whether to extract text from table-type structured documents.
            Types: bool

        enable_images:
            Required Argument.
            Specifies whether to extract text from image documents (captions).
            Types: bool

        enable_infographics:
            Required Argument.
            Specifies whether to extract text from infographic-type structured documents.
            Types: bool

    RETURNS:
        str or None: The extracted text content if valid and within length limits, None otherwise.

    RAISES:
        KeyError: If the element structure is invalid or missing required metadata keys.

    EXAMPLES:
        >>> text_element = {
        ...     "document_type": "text",
        ...     "metadata": {
        ...         "content": "Sample text content",
        ...         "embedding": [0.1, 0.2, 0.3],
        ...         "source_metadata": {"source_name": "doc.txt"},
        ...         "content_metadata": {"page_number": 1}
        ...     }
        ... }
        >>> _pull_text(text_element, True, True, True, True, True)
        'Sample text content'
        
        >>> # Text disabled
        >>> _pull_text(text_element, False, True, True, True, True)
        None
    """
    text = None
    if element["document_type"] == "text" and enable_text:
        text = element["metadata"]["content"]
    elif element["document_type"] == "structured":
        text = element["metadata"]["table_metadata"]["table_content"]
        if element["metadata"]["content_metadata"]["subtype"] == "chart" and not enable_charts:
            text = None
        elif element["metadata"]["content_metadata"]["subtype"] == "table" and not enable_tables:
            text = None
        elif element["metadata"]["content_metadata"]["subtype"] == "infographic" and not enable_infographics:
            text = None
    elif element["document_type"] == "audio" and enable_audio:
            text = element["metadata"]["audio_metadata"]["audio_transcript"]
    elif element["document_type"] == "image" and enable_images:
        text = element["metadata"]["image_metadata"]["caption"]
    verify_emb = verify_embedding(element)
    if not text or not verify_emb:
        source_name = element["metadata"]["source_metadata"]["source_name"]
        pg_num = element["metadata"]["content_metadata"].get("page_number", None)
        doc_type = element["document_type"]
        if not verify_emb:
            logger.debug(f"failed to find embedding for entity: {source_name} page: {pg_num} type: {doc_type}")
        if not text:
            logger.debug(f"failed to find text for entity: {source_name} page: {pg_num} type: {doc_type}")
        # if we do find text but no embedding remove anyway
        text = None
    if text and len(text) > 65535:
        logger.warning(
            f"Text is too long, skipping. It is advised to use SplitTask, to make smaller chunk sizes."
            f"text_length: {len(text)}, "
            f"file_name: {element['metadata']['source_metadata'].get('source_name', None)} "
            f"page_number: {element['metadata']['content_metadata'].get('page_number', None)}"
        )
        text = None
    return text


def _record_dict(id, text, element):
    """
    DESCRIPTION:
        Create a standardized record dictionary for Teradata Vector Store insertion.
        This function transforms element data into the required format for the NV-Ingest
        compatible vector store schema with proper column mapping.
        Notes:
            - This function creates the standard record format for Teradata Vector Store
            - All column names match the schema defined in create_nvingest_schema
            - Used internally by cleanup_records function
            - TDID is now auto-generated by the database, so not included here

    PARAMETERS:
        id:
            Required Argument.
            Specifies the unique identifier for the record (not used, kept for compatibility).
            Types: int

        text:
            Required Argument.
            Specifies the text content to be stored in the text column.
            Can be None if no valid text was extracted.
            Types: str or None

        element:
            Required Argument.
            Specifies the source element containing metadata and embedding information.
            Expected to have 'metadata' with 'embedding' and 'source_metadata' fields.
            Types: dict

    RETURNS:
        Dict[str, Any]: A dictionary with standardized column names and values:
                       - text: Text content
                       - embeddings: Vector embedding
                       - TD_FILENAME: Source filename
                       Note: TDID is auto-generated by the database

    RAISES:
        KeyError: If the element structure is missing required metadata keys.

    EXAMPLES:
        >>> element = {
        ...     "metadata": {
        ...         "embedding": [0.1, 0.2, 0.3],
        ...         "source_metadata": {"source_name": "document.pdf"}
        ...     }
        ... }
        >>> record = _record_dict(1, "Sample text", element)
        >>> print(record)
        {
            'text': 'Sample text',
            'embeddings': [0.1, 0.2, 0.3],
            'TD_FILENAME': 'document.pdf'
        }
    """
    record = {
        "text": text,
        "embeddings": ", ".join(map(str, element["metadata"]["embedding"])),
        "TD_FILENAME": element["metadata"]["source_metadata"]['source_name']
    }
    return record

@collect_queryband(queryband="VS_nvingest_cleanup_records")
def cleanup_records(
    records,
    enable_text: bool = True,
    enable_charts: bool = True,
    enable_tables: bool = True,
    enable_images: bool = True,
    enable_infographics: bool = True,
    enable_audio: bool = True,
    record_func=_record_dict
):
    """
    DESCRIPTION:
        Clean and process raw NV-Ingest records into a standardized format for vector store insertion.
        This function filters records based on document type preferences, validates content and embeddings,
        and converts them into the required format for Teradata Vector Store operations.
        Notes:
            - Records without valid embeddings are automatically filtered out.
            - Text content exceeding 65535 characters is rejected.
            - Single records are automatically converted to lists for processing.
            - Each element gets assigned a sequential ID starting from 0.

    PARAMETERS:
        records:
            Required Argument.
            Specifies the list of raw records or results from NV-Ingest processing.
            Each record should contain document metadata and embeddings.
            Types: list

        enable_text:
            Optional Argument.
            Specifies whether to include text-type documents in the cleaned records.
            Default Value: True
            Types: bool

        enable_charts:
            Optional Argument.
            Specifies whether to include chart-type structured documents.
            Default Value: True
            Types: bool

        enable_tables:
            Optional Argument.
            Specifies whether to include table-type structured documents.
            Default Value: True
            Types: bool

        enable_images:
            Optional Argument.
            Specifies whether to include image documents (using captions).
            Default Value: True
            Types: bool

        enable_infographics:
            Optional Argument.
            Specifies whether to include infographic-type structured documents.
            Default Value: True
            Types: bool

        record_func:
            Optional Argument.
            Specifies the function to use for creating record dictionaries.
            Default Value: _record_dict
            Types: callable

    RETURNS:
        List[Dict[str, Any]]: A list of cleaned and standardized record dictionaries
                             ready for vector store insertion.

    RAISES:
        None

    EXAMPLES:
        >>> raw_records = [
        ...     {
        ...         "document_type": "text",
        ...         "metadata": {
        ...             "content": "Sample content",
        ...             "embedding": [0.1, 0.2, 0.3],
        ...             "source_metadata": {"source_name": "doc.txt"},
        ...             "content_metadata": {"page_number": 1}
        ...         }
        ...     }
        ... ]
        >>> cleaned = cleanup_records(raw_records)
        >>> print(len(cleaned))
        1
        
        # Filter out text documents
        >>> cleaned_no_text = cleanup_records(raw_records, enable_text=False)
        >>> print(len(cleaned_no_text))
        0
    """
    cleaned_records = []
    for result in records:
        if result is not None:
            if not isinstance(result, list):
                result = [result]
            for element in result:
                text = _pull_text(
                    element, enable_text, enable_charts, enable_tables, enable_images, enable_infographics, enable_audio
                )
                if text:
                    element = record_func(0, text, element)  # ID parameter no longer used
                    cleaned_records.append(element)
    return cleaned_records

@collect_queryband(queryband="VS_write_to_nvingest_vector_store")
@docstring_handler(
    common_params = {**NV_INGEST_PARAMS, **COMMON_PARAMS, **MODEL_URL_PARAMS, **COMMON_SEARCH_PARAMS, **HNSW_SEARCH_PARAMS, **KMEANS_SEARCH_PARAMS},
    exclude_params=["model_urls"])
def write_to_nvingest_vector_store(
    records,
    name,
    embeddings_dims=None,
    enable_text: bool = True,
    enable_charts: bool = True,
    enable_tables: bool = True,
    enable_images: bool = True,
    enable_infographics: bool = True,
    enable_audio: bool = True,
    **kwargs):
    """
    DESCRIPTION:
        Process and insert NV-Ingest records into a Teradata Vector Store.
        This function takes raw NV-Ingest records, cleans and filters them based on document type preferences,
        creates a temporary table, and then creates a vector store with the processed data.
        The function handles the complete pipeline from data processing to vector store creation.
        Notes:
        - Monitors vector store creation status with automatic retry logic.
        - Uses primary index on TDID for optimal performance.
        - Logs the number of elements being inserted.
        - Displays DataFrame head and data types for debugging.
        - Waits for vector store creation to complete before returning.

    PARAMETERS:
        records:
            Required Argument.
            Specifies the list of raw records from NV-Ingest processing pipeline.
            Each record should contain document metadata, content, and embeddings.
            Types: list

        name:
            Required Argument.
            Specifies the name for the vector store to be created.
            Types: str
        
        embeddings_dims:
            Required Argument.
            Specifies the number of dimensions to be used for generating the embeddings.
            The value depends on the embeddings model.
            Types: str
        
    RETURNS:
        None: Function performs side effects (creates vector store) and does not return a value.

    RAISES:
        ValueError: If no records with embeddings are detected after filtering.
        Exception: If vector store creation or status checking fails.

    EXAMPLES:
        >>> # Using NV-Ingest Client to process a PDF file and generate records
        >>> from nv_ingest_client.client import Ingestor, NvIngestClient
        >>> 
        >>> # Define the NV-Ingest server endpoint
        >>> hostname = "<NV-Ingest-Server-Hostname>"
        >>> 
        >>> # Define the path to the test PDF file
        >>> test_file = "./teradatagenai/example-data/multimodal_test.pdf"
        >>> 
        >>> # Initialize and configure the Ingestor
        >>> ingestor = ( 
        ...     Ingestor(message_client_hostname=hostname, message_client_port=443)
        ...     .files(test_file)
        ...     .extract(
        ...         extract_text=True,
        ...         extract_tables=True,
        ...         extract_charts=True,
        ...         extract_images=False)
        ...     .embed(text=True, tables=True)
        ... )
        >>> 
        >>> # Generate the records by processing the PDF
        >>> records = ingestor.ingest(batch_size=20)

        >>> # Create a vector store with all record types
        >>> write_to_nvingest_vector_store(records, "my_vector_store", embeddings_dims=1536)
        
        # Include only text and tables, exclude other types
        >>> write_to_nvingest_vector_store(
        ...     records, 
        ...     "text_table_store",
        ...     embeddings_dims=2048,
        ...     enable_text=True,
        ...     enable_charts=False,
        ...     enable_tables=True,
        ...     enable_images=False,
        ...     enable_infographics=False
        ... )
    """
    # Validating params

    recreate = kwargs.pop("recreate", False)
    arg_info_matrix = []
    arg_info_matrix.append(["records", records, False, (list), True])
    arg_info_matrix.append(["name", name, False, (str), True])
    arg_info_matrix.append(["embeddings_dims", embeddings_dims, False, (int), True])
    arg_info_matrix.append(["enable_text", enable_text, True, (bool)])
    arg_info_matrix.append(["enable_charts", enable_charts, True, (bool)])
    arg_info_matrix.append(["enable_tables", enable_tables, True, (bool)])
    arg_info_matrix.append(["enable_images", enable_images, True, (bool)])
    arg_info_matrix.append(["enable_infographics", enable_infographics, True, (bool)])
    arg_info_matrix.append(["enable_audio", enable_audio, True, (bool)])
    arg_info_matrix.append(["recreate", recreate, True, (bool)])

    _Validators._validate_missing_required_arguments(arg_info_matrix)
    _Validators._validate_function_arguments(arg_info_matrix)

    cleaned_records = cleanup_records(
        records,
        enable_text=enable_text,
        enable_charts=enable_charts,
        enable_tables=enable_tables,
        enable_images=enable_images,
        enable_infographics=enable_infographics,
        enable_audio=enable_audio
    )
    num_elements = len(cleaned_records)
    if num_elements == 0:
        raise ValueError("No records with Embeddings to insert detected.")
    logger.info(f"{num_elements} elements to insert to Teradata Vector Store")
    
    # Create DataFrame with proper data types specified directly (columns are always constant)
    df = pd.DataFrame(cleaned_records).astype({
        'TD_FILENAME': 'string',  # Pandas string dtype for VARCHAR compatibility
        'text': 'string',         # Pandas string dtype for CLOB compatibility
        'embeddings': 'string'    # String for vector data (comma-separated values)
    })
    
    GenAIUtilFuncs._set_queryband()
    
    # Generate the name of the table.
    table_name = UtilFuncs._generate_temp_table_name(prefix="tdgenai_nv_ingest_",
                                                     gc_on_quit=False)
    
    # Create table with auto-incrementing ID using DDL directly
    create_table_ddl = f"""
    CREATE TABLE {table_name} (
        TDID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 MINVALUE 1 MAXVALUE 2147483647 NO CYCLE),
        text VARCHAR(32000) CHARACTER SET UNICODE,
        embeddings VECTOR,
        TD_FILENAME VARCHAR(10000) CHARACTER SET UNICODE
    ) PRIMARY INDEX (TDID)
    """
    
    # Execute the DDL to create the table
    UtilFuncs._execute_ddl_statement(create_table_ddl)
    
    # Insert data without TDID (it will be auto-generated)
    copy_to_sql(df, table_name, if_exists='append', index=False, match_column_order=False)

    
    from teradatagenai import VectorStore
    vec_ins = VectorStore(name=name)
    
    if recreate==False and vec_ins.exists:
        vec_ins.update(object_names=table_name,
                       alter_operation="ADD",
                       **kwargs)
    else:
        if vec_ins.exists:
            vec_ins.destroy()
            # Wait for destruction to complete.
            while True:
                try:
                    status = vec_ins.status()
                    print(f"Vector Store '{name}' creation status: {status}")
                except Exception as e:
                    raise e
                if status is not None:
                    time.sleep(20)
                else:
                    break
        vec_ins.create(object_names=table_name,
                       description=kwargs.pop("description", "nv_ingest_vector_store"),
                       key_columns=['TDID'],
                       data_columns=['embeddings'],
                       embedding_data_columns=['text'],
                       is_embedded=True,
                       embeddings_dims=embeddings_dims,
                       **kwargs)

    while True:
        try:
            status = vec_ins.status()
            print(f"Vector Store '{name}' creation status: {status}")
        except Exception as e:
            raise e
        if 'retry_after' in status:
            time.sleep(20)
        else:
            break

@collect_queryband(queryband="VS_nvingest_retrieval")
@docstring_handler(
common_params = {**SIMILARITY_SEARCH_PARAMS},
exclude_params=["return_type"]
)
def nvingest_retrieval(
    name,
    queries,
    embedding_endpoint=None,
    model_name=None,
    nvidia_api_key=None,
    **kwargs):
    """
    DESCRIPTION:
        Perform vector similarity search using NVIDIA embedding models against a Teradata Vector Store.
        This function embeds query text using NVIDIA's embedding service and searches for similar
        documents in the specified vector store. It handles the complete retrieval pipeline from 
        query embedding to similarity search execution.
        Notes:
            - Requires a valid NVIDIA API key for embedding service access.
            - Performs embedding generation for each provided query.
            - Returns search results for each query in the same order.
            - Additional search parameters can be passed through kwargs.

    PARAMETERS:
        name:
            Required Argument.
            Specifies the name of the vector store to search against.
            Types: str
        
        queries:
            Required Argument.
            Specifies the list of query strings to embed and search with.
            Types: str or list of str
        
        embedding_endpoint:
            Optional Argument.
            Specifies the NVIDIA embedding service endpoint URL.
            If not supplied it extracts from nv_ingest_client's default configuration.
            Types: str
        
        model_name:
            Optional Argument.
            Specifies the NVIDIA embedding model name to use.
            If not supplied it extracts from nv_ingest_client's default configuration.
            Types: str
        
        nvidia_api_key:
            Optional Argument.
            Specifies the API key for authenticating with NVIDIA embedding services.
            If not specified, checks the environment variable `NVIDIA_API_KEY`.
            Types: str
        
        top_k:
            Optional Argument.
            Specifies the maximum number of results to return per query.
            Default Value: 10
            Types: int

    RETURNS:
        list: A list of search results corresponding to each input query. 
              Each element contains the similarity search results for one query.

    RAISES:
        TeradataGenAIException: If the vector store cannot be accessed or does not exist.
        ValueError: If the embedding process fails due to invalid credentials or service issues.
        
    EXAMPLES:
        >>> from teradatagenai.vector_store.nv_ingest_client import nvingest_retrieval
        
        # Example 1: Basic similarity search with default parameters.
        >>> results = nvingest_retrieval(
        ...     name="my_vectorstore",
        ...     queries="What is machine learning?",
        ...     embedding_endpoint="https://api.nvidia.com/v1/embeddings",
        ...     model_name="nvidia-embedding-model",
        ...     nvidia_api_key="your_nvidia_api_key"
        ... )
        
        # Example 2: Similarity search with multiple queries using NVIDIA's 
        # default endpoint and embedding model.
        >>> results = nvingest_retrieval(
        ...     name="my_vectorstore",
        ...     queries=["What is deep learning?",
        ...              "How does natural language processing work?"],
        ...     nvidia_api_key="your_nvidia_api_key"
        ... )

        
        # Example 3: Similarity search with additional search parameters.
        >>> results = nvingest_retrieval(
        ...     name="my_vectorstore", 
        ...     queries="Explain vector databases",
        ...     top_k=3,
        ...     embedding_endpoint="https://api.nvidia.com/v1/embeddings",
        ...     model_name="nvidia-embedding-model"
        ... )
    """
    from nv_ingest_client.util.util import ClientConfigSchema
    client_config = ClientConfigSchema()

    nvidia_api_key = nvidia_api_key if nvidia_api_key is not None else client_config.nvidia_api_key
    embedding_endpoint = embedding_endpoint if embedding_endpoint is not None else client_config.embedding_nim_endpoint
    model_name = model_name if model_name is not None else client_config.embedding_nim_model_name

    # Validating params
    arg_info_matrix = []
    arg_info_matrix.append(["name", name, False, (str), True])
    arg_info_matrix.append(["queries", queries, False, (str, list), True])
    arg_info_matrix.append(["embedding_endpoint", embedding_endpoint, True, (str), True])
    arg_info_matrix.append(["model_name", model_name, True, (str), True])
    arg_info_matrix.append(["nvidia_api_key", nvidia_api_key, True, (str), True])

    _Validators._validate_missing_required_arguments(arg_info_matrix)
    _Validators._validate_function_arguments(arg_info_matrix)
    
    vs = VectorStore(name=name)
    # embedd the queries based on the provided embedding model and search
    # for the results in VectorStore.
    from llama_index.embeddings.nvidia import NVIDIAEmbedding
    embed_model = NVIDIAEmbedding(base_url=embedding_endpoint, model=model_name, 
                                 nvidia_api_key=nvidia_api_key)
    res = []
    queries = UtilFuncs._as_list(queries)

    for query in queries:
        query_embedding = embed_model.get_query_embedding(query)
        query_embedding = ','.join(list(map(lambda x: str(x), query_embedding)))
        result = vs.similarity_search_by_vector(question=query_embedding, **kwargs)
        result.similar_objects = result.similar_objects.filter(items = ['TDID', 'text', 'score'])
        res.append(result)

    return res

