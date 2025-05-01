# compare.py


import time
import numpy as np
import psutil
from sentence_transformers import SentenceTransformer
import redis
import chromadb
import faiss
import os
import glob

# ---------- Document Ingestion from Folder ----------
folder_path = './backend/processed'  
file_pattern = os.path.join(folder_path, "*_chunk_500_overlap_50.txt")
file_list = glob.glob(file_pattern)

documents = []
for file_path in file_list:
    with open(file_path, "r", encoding="utf8") as f:
        text = f.read().strip()
        documents.append(text)

print(f"Loaded {len(documents)} documents.")

model = SentenceTransformer("all-MiniLM-L6-v2")

query = "Explain b+ tree"  

doc_embeddings = model.encode(documents)
query_embedding = model.encode([query])[0]

def check_memory():
    process = psutil.Process()
    mem_mb = process.memory_info().rss / (1024 ** 2)
    return mem_mb

### Redis Vector DB Setup ###
redis_client = redis.Redis(host='localhost', port=6385)  
VECTOR_DIM = len(doc_embeddings[0])

redis_client.flushdb()
redis_client.execute_command(f"""
FT.CREATE idx ON HASH PREFIX 1 doc:
SCHEMA text TEXT 
embedding VECTOR HNSW 6 DIM {VECTOR_DIM} TYPE FLOAT32 DISTANCE_METRIC COSINE
""")

# Indexing documents into Redis
start_time = time.time()
for idx, emb in enumerate(doc_embeddings):
    redis_client.hset(f"doc:{idx}", mapping={
        "text": documents[idx],
        "embedding": np.array(emb, dtype=np.float32).tobytes()
    })
redis_index_time = time.time() - start_time
redis_memory = check_memory()

base_query = "*=>[KNN 3 @embedding $vec AS dist]"
query_params = {"vec": np.array(query_embedding, dtype=np.float32).tobytes()}

start_time = time.time()
from redis.commands.search.query import Query

q = (
    Query(base_query)
    .return_fields("text", "dist")
    .sort_by("dist")
    .dialect(2)
)
res = redis_client.ft("idx").search(q, query_params=query_params)
redis_query_time = time.time() - start_time

print("Redis search results:")
for doc in res.docs:
    print(f"Doc ID: {doc.id}, Distance: {doc.dist}")
    print("Text preview:", doc.text[:200], "...\n")

### Chroma DB Integration ###
chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="test_collection")

start_time = time.time()
collection.add(
    embeddings=doc_embeddings.tolist(),
    documents=documents,
    ids=[f"id{i}" for i in range(len(documents))]
)
chroma_index_time = time.time() - start_time
chroma_memory = check_memory()

start_time = time.time()
results_chroma = collection.query(
    query_embeddings=[query_embedding.tolist()],
    n_results=3
)
chroma_query_time = time.time() - start_time

print("\nChroma DB search results:")
print(results_chroma)

### Faiss Integration ###
faiss_index = faiss.IndexFlatL2(VECTOR_DIM)

start_time = time.time()
faiss_index.add(np.array(doc_embeddings).astype('float32'))
faiss_index_time = time.time() - start_time
faiss_memory = check_memory()

start_time = time.time()
D, I = faiss_index.search(np.array([query_embedding]).astype('float32'), k=3)
faiss_query_time = time.time() - start_time

print("\nFaiss search results:")
for distance, index in zip(D[0], I[0]):
    print(f"Doc Index: {index}, Distance: {distance}")

## Performance Comparison Results ##
print("\n--- Performance Comparison ---")
print(f"{'Metric':<20} {'Redis':<10} {'Chroma':<10} {'Faiss':<10}")
print(f"{'-'*50}")
print(f"{'Indexing Time (s)':<20} {redis_index_time:<10.4f} {chroma_index_time:<10.4f} {faiss_index_time:<10.4f}")
print(f"{'Query Time (s)':<20} {redis_query_time:<10.4f} {chroma_query_time:<10.4f} {faiss_query_time:<10.4f}")
print(f"{'Memory Usage (MB)':<20} {redis_memory:<10.2f} {chroma_memory:<10.2f} {faiss_memory:<10.2f}")
