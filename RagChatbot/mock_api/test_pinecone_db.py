from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
import pandas as pd
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os
from pinecone_text.sparse import BM25Encoder

df = pd.read_csv('embeddings.csv')
df = df.drop_duplicates(subset='Url', keep='first')

load_dotenv()
bm25 = BM25Encoder()
bm25.fit(df['Text'].tolist())

pinecone_key = os.getenv('PINECONE_API_KEY')
pc = Pinecone(api_key=pinecone_key)
model = SentenceTransformer('Alibaba-NLP/gte-large-en-v1.5', trust_remote_code=True)
index_name = "payactiv-hybrid-index"
index = pc.Index(index_name)

query = "How much can I withdraw from my earned wages"
sparse_vec = bm25.encode_queries(query)
embedding = model.encode(query).tolist()
result = index.query(namespace="", vector=embedding,sparse_vector=sparse_vec, top_k=2, include_metadata=True)
print(result)

arr = result['matches']
output = []
for match in arr:
    output.append(match['metadata']['text'])

print(output)