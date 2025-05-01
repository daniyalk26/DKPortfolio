# Retrieval-Augmented Generation Chatbot (RAG-Chatbot) with BERT Model🤖📚

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

