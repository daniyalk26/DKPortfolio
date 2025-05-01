import pandas as pd
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os
from opensearchpy import OpenSearch
import numpy as np

# Load environment variables from the .env file
load_dotenv()

# Get the environment variables
opensearch_url = 'http://localhost:9200'

# Connect to OpenSearch without authentication and SSL
client = OpenSearch(
    hosts=[opensearch_url],
    use_ssl=False,
    verify_certs=False,
    ssl_show_warn=False
)

# Load the sentence transformer model
model = SentenceTransformer('Alibaba-NLP/gte-large-en-v1.5', trust_remote_code=True)

# Define the index name
index_name = "payactiv-chatbot-index"

def normalize_embedding(embedding):
    norm = np.linalg.norm(embedding)
    if norm == 0:
        return embedding
    return embedding / norm

def query_opensearch(query, index_name):
    # Encode the query
    embedding = model.encode(query)
    normalized_embedding = normalize_embedding(embedding).tolist()

    # Construct the search query
    query_body = {
        "query": {"knn": {"embedding": {"vector": embedding, "k": 3}}},
        "_source": False,
        "fields": ["text"],
    }

    # Execute the search query
    response = client.search(index=index_name, body=query_body)
    
    return response

# Verify Data Insertion
def verify_data_insertion(index_name):
    response = client.search(index=index_name, body={"query": {"match_all": {}}})
    print(f"Total Documents in {index_name}: {response['hits']['total']['value']}")

# Example query
query = "Tell me about Payactiv"
verify_data_insertion(index_name)
result = query_opensearch(query, index_name)

print(result)

# Process and print the results
hits = result['hits']['hits']
print(hits)
output = [hit['_source']['text'] for hit in hits]

print(output)