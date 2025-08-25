import argparse
import psycopg2
import pandas as pd
from dotenv import load_dotenv
import os
from datetime import datetime
from utils import get_text_hash, sanitize_filename, setup_logger
from query_llm import LLMQueryHandler

# Load .env variables
load_dotenv()

logger = setup_logger(__name__)

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", 5432)
OUTPUT_DATA_PATH = os.getenv("OUTPUT_DATA_PATH")
CONTEXT_FILE = os.getenv("CONTEXT_FILE", "data/context.txt")

if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, OUTPUT_DATA_PATH]):
    logger.error("Environment variables for DB or OUTPUT_DATA_PATH are missing")
    raise ValueError("Missing environment variables for DB or OUTPUT_DATA_PATH")

parser = argparse.ArgumentParser(
    description="Generate & execute a SQL query from user prompt using RAG + LLM."
)
parser.add_argument("--user_prompt", required=True, help="User natural language query")
parser.add_argument("--vector_store", required=True, help="pinecone or weaviate")
parser.add_argument("--gpt_model", required=True, help="LLM model for SQL generation")

args = parser.parse_args()

user_prompt = args.user_prompt
vector_store = args.vector_store
gpt_model = args.gpt_model

logger.info(f"User Prompt: {user_prompt}")
logger.info(f"Vector Store: {vector_store}")
logger.info(f"GPT Model: {gpt_model}")


def generate_sql_query(user_prompt: str, vector_store: str, gpt_model: str, embed_model: str) -> str | None:
    """Generate SQL query based on user prompt using LLM + semantic schema."""
    try:
        with open(CONTEXT_FILE, "r") as f:
            context_prompt = f.read()
        handler = LLMQueryHandler(gpt_model, vector_store, embed_model, top_k=3)
        schemas = handler.get_semantic_schemas(user_prompt)
        output = handler.generate_sql_query(schemas, user_prompt, context=context_prompt)
        return output["SQL_QUERY"]
    except Exception as e:
        logger.exception(f"Error in SQL Query Generation: {e}")
        exit(1)


def execute_sql_on_postgres(query: str, params=None) -> pd.DataFrame:
    """Execute SQL query on PostgreSQL database and return result as DataFrame."""
    try:
        connection = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        df = pd.read_sql_query(query, connection, params=params)
        connection.close()
        return df
    except Exception as e:
        logger.exception(f"Error executing SQL on PostgreSQL: {e}")
        exit(1)


embed_model = "text-embedding-3-small"
sql_query = generate_sql_query(user_prompt, vector_store, gpt_model, embed_model)

if sql_query is None:
    logger.error("SQL Query Generation Failed. Exiting.")
    exit(1)

logger.info(f"Generated SQL Query: {sql_query}")

# Run query on PostgreSQL
df = execute_sql_on_postgres(sql_query)

# Save output with hash + timestamp
user_prompt_sanitized = sanitize_filename(user_prompt)
sql_query_hash = get_text_hash(sql_query)
timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

output_file_name = f"query_result_{timestamp_str}_{user_prompt_sanitized}_{sql_query_hash}.csv"
os.makedirs(OUTPUT_DATA_PATH, exist_ok=True)
output_file_path = os.path.join(OUTPUT_DATA_PATH, output_file_name)

df.to_csv(output_file_path, index=False)

logger.info(f"Data saved to {output_file_name}")
