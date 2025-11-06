from teradatagenai.vector_store.vector_store import VSManager, VectorStore, VSPattern, ModelUrlParams, IngestParams
from teradatagenai.vector_store.nv_ingest_client import create_nvingest_schema, write_to_nvingest_vector_store, nvingest_retrieval

# Optional import for TeradataVDB - requires nv-ingest-client
try:
    from teradatagenai.vector_store.teradataVDB import TeradataVDB
    __all__ = ['VSManager', 'VectorStore', 'VSPattern', 'ModelUrlParams', 'IngestParams','create_nvingest_schema', 
               'write_to_nvingest_vector_store', 'nvingest_retrieval', 'TeradataVDB']
except ImportError:
    # TeradataVDB is not available if nv-ingest-client is not installed
    __all__ = ['VSManager', 'VectorStore', 'VSPattern', 'ModelUrlParams', 'IngestParams','create_nvingest_schema', 
               'write_to_nvingest_vector_store', 'nvingest_retrieval']
    TeradataVDB = None

