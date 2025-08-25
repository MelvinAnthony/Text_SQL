import os
import logging
from dotenv import load_dotenv
import pinecone

# Load environment variables
load_dotenv()

# Setup logger
def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    if not logger.hasHandlers():
        logger.addHandler(handler)
    return logger

logger = setup_logger(__name__)

def delete_database(index_name: str, vector_store: str = "pinecone"):
    """
    Deletes an index from Pinecone.

    Parameters:
    ---
    - index_name (str): The name of the index in Pinecone you wish to delete.
    - vector_store (str, optional): Currently only supports Pinecone.
    """
    if vector_store == "pinecone":
        try:
            # Initialize Pinecone client
            PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
            pinecone.init(api_key=PINECONE_API_KEY)

            # Delete the index
            pinecone.delete_index(index_name)

            logger.info(f"Successfully deleted the index '{index_name}' from Pinecone")

        except Exception as e:
            logger.error(f"Error deleting the index '{index_name}' from Pinecone: {str(e)}")


if __name__ == "__main__":
    vector_index_to_delete = "CricketIndex"  # change to your index name
    delete_database(vector_index_to_delete)
