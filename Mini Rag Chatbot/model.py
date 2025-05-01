import os
import glob
import time
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import psutil

folder_path = './backend/processed'
file_pattern = os.path.join(folder_path, "*_chunk_500_overlap_50.txt")
file_list = glob.glob(file_pattern)

def get_memory_usage_in_MB():
    """
    Returns the current process's memory usage in MB.
    """
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

documents = []
for file_path in file_list:
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
        documents.append(text)

queries = [
    "Explain the concept of vector embeddings.",
    "What are the key topics in DS4300 course notes?"
]

models = {
    "all-MiniLM-L6-v2": SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2"),
    "all-mpnet-base-v2": SentenceTransformer("sentence-transformers/all-mpnet-base-v2"),
    "gte-large-en-v1.5": SentenceTransformer("Alibaba-NLP/gte-large-en-v1.5", trust_remote_code=True)
}

def get_embeddings(model, texts, model_name=""):
    """
    Encodes the provided texts into embeddings using the specified model.
    Measures encoding time and memory usage (in MB) during the process.
    
    """
    start_time = time.time()
    mem_before = get_memory_usage_in_MB()

 
   
        # For other models, just truncate everything at 512 tokens
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        truncation=True,
        max_length=512
        )
    
    elapsed_time = time.time() - start_time
    mem_after = get_memory_usage_in_MB()
    mem_used = mem_after - mem_before
    
    return embeddings, elapsed_time, mem_used

def retrieve_top_k(model, query, doc_embeddings, documents, model_name="", k=5):
    """
    Retrieves the top-k most similar documents for a given query
    based on cosine similarity of embeddings.
    """

    query_embedding = model.encode(
        [query],
        truncation=True,
        max_length=512
    )
    
    # Compute cosine similarities and retrieve top-k
    similarities = cosine_similarity(query_embedding, doc_embeddings)[0]
    top_k_idx = np.argsort(similarities)[::-1][:k]
    return [documents[i] for i in top_k_idx]

def main():
    results = {}

    for name, model in models.items():
        print(f"\nEvaluating {name}...")

        doc_embeddings, encoding_time, memory_used = get_embeddings(model, documents, model_name=name)

        top_results = retrieve_top_k(model, queries[0], doc_embeddings, documents, model_name=name)
        
        results[name] = {
            "encoding_time": encoding_time,
            "memory_used_MB": memory_used,
            "top_results": top_results
        }

        print(f"Encoding time: {encoding_time:.2f} seconds")
        print(f"Memory used: {memory_used:.2f} MB")
        print("Top results for query:", queries[0])
        for res in top_results:
            print(" -", res[:200], "...")
    
    return results

if __name__ == "__main__":
    main()
