from llama_index.core import Document
from llama_index.core.schema import TransformComponent
from llama_index.core.ingestion import IngestionPipeline
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.vector_stores.weaviate import WeaviateVectorStore
from llama_index.core import VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from pinecone import Pinecone, ServerlessSpec
import weaviate
import re
from dotenv import load_dotenv
import os
from utils import check_valid_vector_store

load_dotenv()


class CricketSchemaParser(TransformComponent):
    """
    Parse cricket database schemas into smaller Documents
    Example: CREATE TABLE matches (...), CREATE TABLE players (...)
    """

    def __call__(self, docs: list[Document], **kwargs) -> list[Document]:
        processed_docs = []
        for doc in docs:
            schemas = re.split(r";\s*", doc.text)  # split multiple CREATE TABLE statements
            for schema in schemas:
                matched_string = re.search(r"CREATE TABLE (\w+)", schema, re.IGNORECASE)
                if matched_string:
                    title = matched_string.group(1)
                    processed_doc = Document(
                        text=schema.strip(),
                        extra_info={"title": title}
                    )
                    processed_docs.append(processed_doc)
        return processed_docs


def check_weaviate_vector_store_exists(client: weaviate.Client, vector_store_name: str):
    schema = client.schema.get()
    classes = schema.get("classes", [])
    for cls in classes:
        if cls["class"] == vector_store_name:
            return True
    return False


def initialize_vector_store(
    vector_store_name: str,
    pinecone_api_key: str,
    pinecone_config: dict,
    index_name: str = None,
) -> WeaviateVectorStore | PineconeVectorStore:

    WEAVIATE_HOST = os.environ.get("WEAVIATE_HOST")

    if vector_store_name == "weaviate":
        if index_name is None:
            index_name = "CricketSchemaIndex"

        client = weaviate.Client(url=WEAVIATE_HOST)

        if not check_weaviate_vector_store_exists(client, index_name):
            vector_store = WeaviateVectorStore(
                weaviate_client=client, index_name=index_name
            )
        else:
            return False

    elif vector_store_name == "pinecone":
        if pinecone_config is None:
            raise ValueError("pinecone_config must be specified if using Pinecone.")
        elif not isinstance(pinecone_config, dict):
            raise TypeError("pinecone_config must be a dictionary.")

        required_pinecone_configs = ["metric", "dimension", "cloud", "region"]
        if not all(key in pinecone_config for key in required_pinecone_configs):
            raise ValueError("pinecone_config has missing configurations")

        metric = pinecone_config["metric"]
        dimension = pinecone_config["dimension"]
        cloud = pinecone_config["cloud"]
        region = pinecone_config["region"]

        if index_name is None:
            index_name = "cricket-schema-index"

        if not pinecone_api_key:
            raise ValueError("API keys for Pinecone is required.")

        pc = Pinecone(api_key=pinecone_api_key)
        index_names = pc.list_indexes().names()

        if index_name not in index_names:
            pc_index = pc.create_index(
                name=index_name,
                dimension=dimension,
                metric=metric,
                spec=ServerlessSpec(cloud=cloud, region=region),
            )
        else:
            pc_index = pc.Index(name=index_name)

        vector_store = PineconeVectorStore(
            pinecone_index=pc_index,
            index_name=index_name,
            api_key=pinecone_api_key,
        )

    return vector_store


def create_cricket_database(
    file_path: str,
    vector_store_name: str,
    model: str,
    embed_batch_size: int,
    pinecone_config: dict = None,
    index_name: str = None,
) -> VectorStoreIndex:
    """
    Creates and populates a vector database for cricket schemas.
    Reads cricket DB schemas (players, matches, teams, deliveries, etc.)
    and stores embeddings in Pinecone/Weaviate for semantic search.
    """

    if not check_valid_vector_store(vector_store_name):
        raise ValueError(
            f"{vector_store_name} is not supported. Currently supported: 'pinecone' or 'weaviate'"
        )

    pinecone_api_key = os.environ.get("PINECONE_API_KEY")
    if pinecone_api_key is None:
        raise ValueError("PINECONE_API_KEY must be set in environment.")

    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key is None:
        raise ValueError("OPENAI_API_KEY must be set in environment.")

    vector_store = initialize_vector_store(
        vector_store_name, pinecone_api_key, pinecone_config, index_name
    )
    if vector_store:
        pipeline = IngestionPipeline(
            transformations=[
                CricketSchemaParser(),
                OpenAIEmbedding(
                    model=model,
                    api_key=openai_api_key,
                    embed_batch_size=embed_batch_size,
                ),
            ],
            vector_store=vector_store,
        )

        with open(file_path, "r") as f:
            text = f.read()

        initial_docs = [Document(text=text)]
        docs = pipeline.run(documents=initial_docs)

        index = VectorStoreIndex.from_vector_store(vector_store)
        return index
    else:
        return None


if __name__ == "__main__":
    # Path to your cricket schema text file
    file_path = "/Users/melvin/data/cricket_schemas.txt"

    vector_store_name = "pinecone"  
    pinecone_config = {
        "metric": "cosine",
        "dimension": 1536,
        "cloud": "aws",
        "region": "us-west-2",
    }
    embed_batch_size = 10
    model = "text-embedding-3-small"

    index = create_cricket_database(
        file_path, vector_store_name, model, embed_batch_size, pinecone_config
    )
