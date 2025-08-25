from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core import VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from pinecone import Pinecone
from dotenv import load_dotenv
import os
import logging


def setup_logger(name: str):
    """Helper logger setup"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    return logger


def query_database(
    query: str,
    embed_model: str,
    embed_batch_size: int = 10,
    index_name: str = "cricket-index",
    top_k: int = 5,
):
    """
    Queries the Pinecone vector database for items that are similar to a given query.

    Parameters:
    ----
    - query (str): The query string to search for.
    - embed_model (str): OpenAI embedding model name (e.g. "text-embedding-3-small").
    - embed_batch_size (int, optional): The number of docs to process per batch. Default=10.
    - index_name (str, optional): The Pinecone index to query. Default="cricket-index".
    - top_k (int, optional): Number of top similar items to retrieve. Default=5.

    Returns:
    ----
    - A list of nodes representing the top k similar items.
    """

    load_dotenv()

    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not pinecone_api_key:
        raise ValueError("PINECONE_API_KEY must be specified in .env file.")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY must be specified in .env file.")

    # Connect to Pinecone
    pc = Pinecone(api_key=pinecone_api_key)

    if index_name not in pc.list_indexes().names():
        raise ValueError(f"Index '{index_name}' does not exist in Pinecone.")

    pc_index = pc.Index(name=index_name)

    # Wrap Pinecone index
    vector_store = PineconeVectorStore(pinecone_index=pc_index, api_key=pinecone_api_key)

    # Setup retriever
    retriever = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=OpenAIEmbedding(
            model=embed_model, embed_batch_size=embed_batch_size, api_key=openai_api_key
        ),
    ).as_retriever(similarity_top_k=top_k)

    nodes = retriever.retrieve(query)

    return nodes


if __name__ == "__main__":
    logger = setup_logger(__name__)
    query = "Who scored the most runs in match 12 of IPL 2024?"

    try:
        nodes = query_database(
            query=query,
            embed_model="text-embedding-3-small",
            index_name="cricket-index",
            top_k=5,
        )
        for node in nodes:
            title = node.metadata.get("title", "Unknown Table")
            print(f"Table: {title}")
            print(f"Similarity Score: {node.get_score()}")
            print(f"Data: {node.get_text()}")
            print("-" * 40)

    except Exception as e:
        logger.error(f"Failed to query Pinecone: {e}")
