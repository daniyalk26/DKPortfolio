import os
import time
import subprocess
import redis
import numpy as np
from sentence_transformers import SentenceTransformer
from redis.commands.search.query import Query

os.environ["TOKENIZERS_PARALLELISM"] = "false"

redis_client = redis.Redis(host='localhost', port=6385)  # using port 6381

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def retrieve_top_k_from_redis(query_text: str, k: int = 3):
    """
    Embeds the user query and retrieves the top-k most similar documents
    from Redis, returning a list of (text, distance) tuples.
    """
    query_embedding = model.encode([query_text])[0].astype(np.float32)
    base_query = f"*=>[KNN {k} @embedding $vec AS dist]"
    query_params = {"vec": np.array(query_embedding, dtype=np.float32).tobytes()}
    
    q = (
        Query(base_query)
        .return_fields("text", "dist")
        .sort_by("dist")
        .dialect(2)
    )
    results = redis_client.ft("idx").search(q, query_params=query_params)
    
    top_k = []
    for doc in results.docs:
        dist = float(doc.dist)
        top_k.append((doc.text, dist))
    return top_k

def create_prompt(system_prompt: str, context: str, user_query: str) -> str:

    prompt = (
        f"{system_prompt}\n\n"
        "Context:\n"
        f"{context}\n\n"
        "User query:\n"
        f"{user_query}\n\n"
        "Answer:\n"
    )
    return prompt

def generate_response_with_ollama(model_name: str, prompt: str) -> str:

    try:
        command = ["ollama", "run", model_name]
        result = subprocess.run(
            command, 
            input=prompt, 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error running {model_name}: {e}"


def main():
    system_prompt = (
        "You are an assistant that must answer questions ONLY using the text provided below under the 'Context:' section. "
        "Do not add or infer any information from your internal knowledge. If the answer is not clearly stated in the context, respond exactly with: "
        "'No relevant information in my notes.'\n"
        "Answer the following query:"
    )

    while True:
        user_query = input("Enter your query (or 'exit' to quit): ")
        if user_query.strip().lower() == "exit":
            break

        start_time = time.time()    # start timer   
        
        top_docs = retrieve_top_k_from_redis(user_query, k=3)
        
        COSINE_THRESHOLD = 0.8
        if not top_docs or top_docs[0][1] > COSINE_THRESHOLD:
            print("No relevant information in my notes.\n")
            continue

        context = "\n".join(text for text, _ in top_docs)
        prompt = create_prompt(system_prompt, context, user_query)
        
        deepseek_model_name = "deepseek-r1:1.5b"
        llama_model_name = "llama3.2"
        
        response_deepseek = generate_response_with_ollama(deepseek_model_name, prompt)
        response_llama = generate_response_with_ollama(llama_model_name, prompt)

        end_time = time.time()  # end timeer
        elapsed_time = end_time - start_time
        
        # Only show the final outputs
        print("\n=== Final Output ===")
        print("DeepSeek-r1:1.5b:", response_deepseek if response_deepseek else "[No output]")
        print("Llama3.2:", response_llama if response_llama else "[No output]")
        print("\n")

        print(f"\n[INFO] Total time taken: {elapsed_time:.2f} seconds\n")
    
if __name__ == "__main__":
    main()
