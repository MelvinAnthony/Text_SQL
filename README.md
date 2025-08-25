# 🏏 RAG-Based Intelligent Cricket Analytics System

This repository implements a Retrieval-Augmented Generation (RAG) powered system that allows users to query cricket analytics data in natural language and automatically generate SQL queries for PostgreSQL. The system integrates Pinecone, PostgreSQL, OpenAI embeddings, and LLMs (OpenAI, Claude, Ollama) to provide intelligent data retrieval, execution, and visualization.

---

## 📌 Features
- **RAG Framework**: Combines vector similarity search with LLMs for context-aware SQL query generation.
- **Cricket Data Analysis**: Stores structured cricket match data in PostgreSQL for advanced analytics.
- **OpenAI Embeddings**: Converts queries and cricket records into embeddings for semantic similarity.
- **Vector Search with Pinecone**: Retrieves relevant cricket records efficiently using KNN with cosine similarity.
- **Multi-LLM SQL Generation**: Uses OpenAI, Claude, and Ollama to generate and compare SQL queries.
- **Query Validation & Optimization**: Ensures generated SQL is syntactically correct before execution.
- **Streamlit Interface**: Provides a user-friendly dashboard for query input and result visualization.

---
<img width="1534" height="791" alt="image" src="https://github.com/user-attachments/assets/33d79f1f-3741-435c-a49b-751e2651c7d8" />


## ⚙️ System Workflow

<img width="787" height="788" alt="image" src="https://github.com/user-attachments/assets/99929c99-7e6d-4d9d-b859-4789f211e862" />

---

## 🛠️ Tech Stack
- **Database**: PostgreSQL
- **Vector Database**: Pinecone
- **Embeddings**: OpenAI
- **LLMs**: OpenAI, Claude, Ollama
- **Frontend**: Streamlit
- **Language**: Python


## 📂 Project Structure
```
├── data/                  # Cricket dataset
├── utils/                 # Utility functions.
├── embeddings/            # Embedding generation & storage
├── query/                 # SQL generation & validation
├── app.py                 # Streamlit interface
├── requirements.txt       # Dependencies
├── README.md              # Documentation
└── .env                   # API keys and DB configs
```

---

## 📊 Example Query Flow
- **Input**: "Show me top 5 highest scorers in IPL 2020."
- **Semantic Search**: Pinecone retrieves relevant cricket match records.
- **LLM Output**: Generates SQL query → `SELECT player, SUM(runs) FROM matches WHERE season=2020 GROUP BY player ORDER BY SUM(runs) DESC LIMIT 5;`
- **Execution**: PostgreSQL returns the results.
- **UI**: Streamlit displays the result table.

---

## 📈 Future Enhancements
- Add visualization (bar/line charts) for query results.
- Extend support for player career stats, strike rates, and bowling analytics.
- Optimize query generation using reinforcement learning.

---


