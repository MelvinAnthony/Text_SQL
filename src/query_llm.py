from openai import OpenAI
import anthropic
import pandas as pd
import psycopg2
import re
import os
from query_vector_database import query_database


class LLMQueryHandler:
    """
    A handler for querying Pinecone vector DB + PostgreSQL using LLM-generated SQL.
    """

    def __init__(
        self,
        model: str,
        vector_store: str,
        embed_model: str,
        db_params: dict,
        index_name: str = None,
        top_k=5,
    ):
        self.model = model
        self.vector_store = vector_store  # should be "pinecone"
        self.embed_model = embed_model
        self.db_params = db_params  # dict: {user, password, host, port, dbname}
        self.index_name = index_name
        self.top_k = top_k
        self.messages = []

    def get_semantic_schemas(self, user_prompt: str) -> list[str]:
        nodes = query_database(
            query=user_prompt,
            vector_store=self.vector_store,
            embed_model=self.embed_model,
            index_name=self.index_name,
            top_k=self.top_k,
        )
        return [node.get_text() for node in nodes]

    def generate_initial_query(self, schemas: list[str], user_prompt: str, context: str, system_prompt: str = None):
        if system_prompt is None:
            system_prompt = self._create_system_prompt(schemas, context)

        model_service = self._find_model()
        if model_service == "gpt":
            self.messages.append({"role": "system", "content": system_prompt})
            self.messages.append({"role": "user", "content": user_prompt})
        elif model_service == "claude":
            self.messages.append({"role": "user", "content": user_prompt})

    def generate_sql_query(self) -> dict:
        if self._find_model() == "gpt":
            openai_api_key = os.environ.get("OPENAI_API_KEY")
            if openai_api_key is None:
                raise ValueError("OPENAI_API_KEY must be set.")

            self.client = OpenAI(api_key=openai_api_key)
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
            )
            sql_query = completion.choices[0].message.content
            n_generated_tokens = completion.usage.completion_tokens
            n_prompt_tokens = completion.usage.prompt_tokens
            model = completion.model
            return {
                "SQL_QUERY": sql_query,
                "MODEL": model,
                "N_PROMPT_TOKENS": n_prompt_tokens,
                "N_GENERATED_TOKENS": n_generated_tokens,
            }

        elif self._find_model() == "claude":
            claude_api_key = os.environ.get("CLAUDE_API_KEY")
            if claude_api_key is None:
                raise ValueError("CLAUDE_API_KEY must be set.")

            client = anthropic.Anthropic(api_key=claude_api_key)
            message = client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=self.system_prompt,
                messages=self.messages,
            )
            sql_query = message.content[0].text
            return {
                "SQL_QUERY": sql_query,
                "MODEL": message.model,
                "N_PROMPT_TOKENS": message.usage.input_tokens,
                "N_GENERATED_TOKENS": message.usage.output_tokens,
            }

    def execute_sql_on_db(self, query: str, params=None) -> tuple[pd.DataFrame | None, None | str]:
        """Executes SQL query on PostgreSQL and returns DataFrame."""
        try:
            conn = psycopg2.connect(
                dbname=self.db_params["dbname"],
                user=self.db_params["user"],
                password=self.db_params["password"],
                host=self.db_params["host"],
                port=self.db_params["port"],
            )
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            return df, None
        except Exception as e:
            return None, str(e)

    def _find_model(self):
        match = re.search(r"(gpt|claude)", self.model)
        return match.group() if match else None

    def _find_claude_model(self):
        if self._find_model() == "claude":
            match = re.search(r"(opus|sonnet|haiku)", self.model)
            return match.group() if match else None
        return None

    def _create_system_prompt(self, schemas: list[str], context: str) -> str:
        self.system_prompt = f"""
        You are an expert SQL assistant for a Cricket Analytics Database (PostgreSQL).

        SQL Schema:
        {schemas}

        {context}

        - Only output valid SQL queries.
        - Do NOT explain, only return SQL.
        """
        return self.system_prompt
