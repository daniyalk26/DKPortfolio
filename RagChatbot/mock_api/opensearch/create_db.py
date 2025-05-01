
import pandas as pd
from dotenv import load_dotenv
import os
from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk
import numpy as np

opensearch_url = 'http://localhost:9200'

# Load your data
df = pd.read_csv('../embeddings.csv')
df = df.drop_duplicates(subset='Url', keep='first')

# Normalize the embeddings
def normalize_embedding(embedding):
    norm = np.linalg.norm(embedding)
    if norm == 0:
        return embedding
    return embedding / norm

# Connect to OpenSearch without authentication and SSL
client = OpenSearch(
    hosts=[opensearch_url],
    use_ssl=False,
    verify_certs=False,
    ssl_show_warn=False
)

# Define the index name
index_name = "payactiv-chatbot-index"

# Create an index with a vector field if it doesn't exist
if not client.indices.exists(index=index_name):
    index_body = {
    "settings": {
        "index": {
        "knn": True,
        "knn.algo_param.ef_search": 100
        }
    },
    "mappings": { #how do we store, 
        "properties": {
            "embedding": {
            "type": "knn_vector", #we are going to put 
            "dimension": 1024,
            "method": {
                "name": "hnsw",
                "space_type": "l2",
                "engine": "nmslib",
                "parameters": {
                "ef_construction": 128,
                "m": 24
                }
            }
        }
    }
    }}

    client.indices.create(index=index_name, body=index_body)

# Prepare the data for upserting
upsert_data = [
    {
        '_op_type': 'index',
        '_index': index_name,
        '_id': str(i),
        '_source': {
            'text': row['Text'],
            'embedding': row['Embedding'].split(',')
        }
    }
    for i, row in df.iterrows()
]

# Upsert the data into OpenSearch
bulk(client, upsert_data, index=index_name)
