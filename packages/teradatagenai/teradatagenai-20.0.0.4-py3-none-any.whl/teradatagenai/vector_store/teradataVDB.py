"""
Copyright (c) 2025 by Teradata Corporation. All rights reserved.
TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET

Primary Owner: aanchal.kavedia@teradata.com
Secondary Owner: Sushant.Mhambrey@Teradata.com
NVIDIA NV-Ingest VDB class for Teradata Vector Store.

This file implements TeradataVDB class that extends the abstract VDB class from 
NVIDIA NV-Ingest along with it's methods.
"""

from nv_ingest_client.util.vdb.adt_vdb import VDB
from teradatagenai.utils.doc_decorator import docstring_handler
from teradataml.telemetry_utils.queryband import collect_queryband
from teradatagenai.common.constants import NVIngestSchemaColumns, COMMON_PARAMS, FILE_BASED_VECTOR_STORE_PARAMS,SIMILARITY_SEARCH_PARAMS,\
                                           MODEL_URL_PARAMS, INGEST_PARAMS, COMMON_SEARCH_PARAMS, KMEANS_SEARCH_PARAMS, HNSW_SEARCH_PARAMS,\
                                           NV_INGEST_PARAMS
from teradatagenai.vector_store.nv_ingest_client import create_nvingest_schema, write_to_nvingest_vector_store, nvingest_retrieval

class TeradataVDB(VDB):
    """
    Implementation of NV-Ingest abstract VDB class that helps integrate 
    Teradata Vector Store into the NVIDIA NV-Ingest processing pipeline.
    This class provides methods to create, write to, and query a Teradata
    Vector Store compatible with the NVIDIA NV-Ingest processing pipeline.
    """
    @docstring_handler(
    common_params = {**NV_INGEST_PARAMS, **COMMON_PARAMS, **MODEL_URL_PARAMS, **COMMON_SEARCH_PARAMS, **HNSW_SEARCH_PARAMS, **KMEANS_SEARCH_PARAMS},
    exclude_params=["model_urls", "ingest_params"])
    def __init__(self, **kwargs):
        """
        DESCRIPTION:
            Initialize a Teradata Vector Database instance.

        PARAMETERS:
            name:
                Optional Argument.
                Specifies the name of the vector store/schema to create.
                Default Value: "nv_ingest_vector_store"
                Types: str

            recreate:
                Optional Argument.
                Specifies whether to recreate the schema if it already exists.
                If True, destroys existing vector store before creating new one.
                Default Value: False
                Types: bool
            
            embeddings_dims:
                Required Argument.
                Specifies the number of dimensions to be used for generating the embeddings.
                The value depends on the embeddings model.
                Types: str

        RETURNS:
            None

        RAISES:
            None

        EXAMPLES:
            >>> from nv_ingest_client.util.vdb.teradata import Teradata
            
            # Example 1: Create a Teradata VDB with a custom name.
            >>> teradata_vdb = Teradata(name="custom_vector_store")
        """
        self.name = kwargs.pop("name", "nv_ingest_vector_store")
        kwargs = locals().copy()
        kwargs.pop("self", None)
        super().__init__(**kwargs)
    
    @collect_queryband(queryband="VS_NVIngest_VDB_create_index")
    def create_index(self, recreate=False, **kwargs):
        """
        DESCRIPTION:
            Create a default schema for Teradata Vector Store compatible with NVIDIA NV-Ingest.
            This method creates a schema structure with fields for embeddings and metadata
            that are specific to Teradata Vector Store implementation.

        PARAMETERS:
            recreate:
                Optional Argument.
                Specifies whether to recreate the schema if it already exists.
                If True, destroys existing vector store before creating a new one.
                Default Value: False
                Types: bool

            **kwargs:
                Optional Argument.
                Additional keyword arguments for schema configuration.
                Types: Any

        RETURNS:
            Dict[str, Any]: A dictionary containing the data type mapping for the schema
                           with column definitions for TDID, TD_FILENAME, text, and embeddings.

        RAISES:
            TeradataGenAIException: If the vector store already exists and recreate is False.

        EXAMPLES:
            >>> from nv_ingest_client.util.vdb.teradata import Teradata
            
            # Example 1: Create a new schema with default settings
            >>> teradata_vdb = Teradata(name="my_vectorstore")
            >>> schema = teradata_vdb.create_index()
            
            # Example 2: Create schema without recreating existing vector store
            >>> schema = teradata_vdb.create_index(recreate=False)
        """
        return create_nvingest_schema(name=self.name, recreate=recreate, **kwargs)
    
    @collect_queryband(queryband="VS_NVIngest_VDB_write_to_index")
    @docstring_handler(
    common_params = {**NV_INGEST_PARAMS, **COMMON_PARAMS, **MODEL_URL_PARAMS, **COMMON_SEARCH_PARAMS, **HNSW_SEARCH_PARAMS, **KMEANS_SEARCH_PARAMS},
    exclude_params=["model_urls", "ingest_params"])
    def write_to_index(self, records: list, **kwargs):
        """
        DESCRIPTION:
            Write records extracted from NV-Ingest output to the Teradata Vector Store.
            This method processes the records and stores them in the vector store with
            their associated embeddings and metadata.

        PARAMETERS:
            records:
                Required Argument.
                A list of records extracted from NV-Ingest output to be written to the vector store.
                Each record should contain text content and associated metadata.
                Types: list
            
            embeddings_dims:
                Required Argument.
                Specifies the number of dimensions to be used for generating the embeddings.
                The value depends on the embeddings model.
                Types: str

        RETURNS:
            None

        RAISES:
            None

        EXAMPLES:
            >>> from nv_ingest_client.util.vdb.teradata import Teradata
            
            # Example: Write records to the vector store
            >>> teradata_vdb = Teradata(name="my_vectorstore")
            >>> teradata_vdb.write_to_index(records=my_records)
            
            # Example with additional parameters.
            >>> teradata_vdb.write_to_index(records=my_records,
                                            batch_size=100,
                                            enable_images=True)
        """
        write_to_nvingest_vector_store(name=self.name, records=records, **kwargs)

    @collect_queryband(queryband="VS_NVIngest_VDB_retrieval")
    def retrieval(self, queries: list, **kwargs):
        """
        DESCRIPTION:
            Perform similarity search on the Teradata Vector Store and return results.
            This method queries the vector store using the provided queries and returns
            the most similar documents based on vector similarity.

        PARAMETERS:
            queries:
                Required Argument.
                A list of query strings to search for in the vector store.
                Types: list

            **kwargs:
                Optional Argument.
                Additional keyword arguments for configuring the retrieval operation,
                such as limit, filter conditions, etc.
                Types: Any

        RETURNS:
            Results of the similarity search from the Teradata Vector Store.

        RAISES:
            None

        EXAMPLES:
            >>> from nv_ingest_client.util.vdb.teradata import Teradata
            
            # Example: Basic retrieval
            >>> teradata_vdb = Teradata(name="my_vectorstore")
            >>> results = teradata_vdb.retrieval(queries=["What is machine learning?"])
            
        """
        nvingest_retrieval(name=self.name, queries=queries, **kwargs)

    @collect_queryband(queryband="VS_NVIngest_VDB_reindex")
    def reindex(self, records: list, **kwargs):
        """
        DESCRIPTION:
            Reindex records and create a new collection in the Teradata Vector Store.
            This method allows for recreating the index with updated records or
            different indexing parameters.

        PARAMETERS:
            records:
                Required Argument.
                A list of records to be reindexed in the vector store.
                Types: list

            **kwargs:
                Optional Argument.
                Additional keyword arguments for configuring the reindexing operation.
                Types: Any

        RETURNS:
            None

        RAISES:
            None

        EXAMPLES:
            >>> from nv_ingest_client.util.vdb.teradata import Teradata
            
            # Example: Reindex with updated records
            >>> teradata_vdb = Teradata(name="my_vectorstore")
            >>> teradata_vdb.reindex(records=updated_records)
        """
        pass

    @collect_queryband(queryband="VS_NVIngest_VDB_run")
    def run(self, records):
        """
        DESCRIPTION:
            Combine creation of the vector store and writing of records in one operation.
            This method provides a convenient way to set up a new vector store and
            populate it with records in a single step.

        PARAMETERS:
            records:
                Required Argument.
                A list of records to be written to the vector store.
                Types: list

        RETURNS:
            None

        RAISES:
            None

        EXAMPLES:
            >>> from nv_ingest_client.util.vdb.teradata import Teradata
            
            # Example: Create vector store and write records in one step
            >>> teradata_vdb = Teradata(name="my_vectorstore")
            >>> teradata_vdb.run(records=my_records)
            
            # Example with recreate=False
            >>> teradata_vdb = Teradata(name="existing_vectorstore", recreate=False)
            >>> teradata_vdb.run(records=new_records)
        """
        write_params = self.__dict__.copy()['kwargs']
        write_params['recreate'] = write_params.get('recreate', False)
        self.create_index(recreate=write_params.get('recreate'))
        self.write_to_index(records, **write_params)