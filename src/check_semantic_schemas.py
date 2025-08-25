import os
import pandas as pd
from openai import OpenAI
import pinecone
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Read API keys from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize Pinecone
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
index = pinecone.Index(PINECONE_INDEX)


def embed_query(query: str, embed_model: str = "text-embedding-3-small") -> list:
    """Generate embedding for user query using OpenAI embeddings."""
    response = client.embeddings.create(model=embed_model, input=query)
    return response.data[0].embedding


def query_pinecone(user_query: str, top_k: int = 5, embed_model: str = "text-embedding-3-small"):
    """Query Pinecone with user query and return top-k schema matches with metadata."""
    query_embedding = embed_query(user_query, embed_model)
    results = index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
    return results["matches"]


def write_user_query_and_semantic_schema_to_file(
    user_query: str, top_k: int = 5, embed_model: str = "text-embedding-3-small"
) -> pd.DataFrame:
    """Store semantic schema context with similarity score for a cricket query."""
    items = []
    nodes = query_pinecone(user_query, top_k=top_k, embed_model=embed_model)

    for node in nodes:
        items.append(
            {
                "UserQuery": user_query,
                "Schema": node["metadata"].get("schema", ""),
                "Table": node["metadata"].get("table", ""),
                "SimilarityScore": node["score"],
            }
        )

    return pd.DataFrame(items)


def compile_queries_to_csv(
    user_queries: list[str],
    output_file_path: str,
    top_k: int = 5,
    embed_model: str = "text-embedding-3-small",
):
    """Compile multiple cricket queries and their semantic schema into one CSV file."""
    dfs = [
        write_user_query_and_semantic_schema_to_file(query, top_k, embed_model)
        for query in user_queries
    ]
    df = pd.concat(dfs, ignore_index=True)
    df.to_csv(output_file_path, index=False)


if __name__ == "__main__":
    output_file_path = "cricket_query_schema_semantic_score.csv"

    user_queries = [
        "How many runs did Virat Kohli score in match 12 during the first innings?",
        "Which bowler took the most wickets in match 45?",
        "What is the strike rate of Rohit Sharma across all matches?",
        "List the top 5 highest run scorers in IPL 2024 season.",
        "Which team has the best bowling economy in powerplay overs?",
    ]

    compile_queries_to_csv(user_queries, output_file_path, top_k=5)
