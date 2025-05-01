# Retrieval-Augmented Generation Chatbot (RAG-Chatbot) 🤖📚

**Ask questions → get answers with citations.**  
This project ingests your unstructured documents, stores semantic embeddings
in a vector database, retrieves the most relevant passages at query time,
and feeds them—along with chat history—into an LLM to generate grounded,
reference-backed responses.

---

## ✨ Key Features

- **Multi-format ingest** – PDF, Markdown, HTML, plaintext.
- **Chunking + embeddings** – uses `tiktoken` splitter and OpenAI
  `text-embedding-3-large` (configurable).
- **Pluggable vector store** – FAISS by default; swap for Pinecone or
  Weaviate by changing one line.
- **Citations** – every answer links to the exact source snippets.
- **FastAPI backend** – stateless `/chat` endpoint returns streaming tokens.
- **UI options** – minimal React/Tailwind client _or_ Streamlit prototype.
- **Docker & Serverless** – run locally (`docker compose up`) or on AWS Lambda
  (via Mangum).

---

## 🏗️ Project Layout

```text
RagChatbot/
├── ingest.py         # ETL: load → split → embed → index
├── api.py            # FastAPI app with /chat route
├── llm.py            # LLM wrapper + prompt templates
├── vector_store/     # Serialized FAISS index lives here
├── ui/               # React front-end (optional)
├── tests/            # pytest unit tests
├── Dockerfile
└── docker-compose.yml
```
