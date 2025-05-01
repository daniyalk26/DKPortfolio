from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
import pandas as pd
from dotenv import load_dotenv
import os
from pinecone_text.sparse import BM25Encoder

load_dotenv()

pinecone_key = os.getenv('PINECONE_API_KEY')

df = pd.read_csv('embeddings.csv')
df = df.drop_duplicates(subset='Url', keep='first')


pc = Pinecone(api_key=pinecone_key)

index_name = "payactiv-hybrid-index"

if index_name not in pc.list_indexes().names():

    pc.create_index(
        name=index_name,
        dimension=1024,
        metric="dotproduct",
        spec=ServerlessSpec(
            cloud='aws', 
            region='us-east-1'
        ) 
    )

index = pc.Index(index_name)

bm25 = BM25Encoder()
sparse_vec = bm25.fit(df['Text'].tolist())

# upsert_data = [
#     (str(i), list(map(float, row['Embedding'].split(','))), {'text': row['Text']})
#     for i, row in df.iterrows()
# ]

upsert_data = []

for i, row in df.iterrows():
   sparse_vec = bm25.encode_documents(row["Text"])
   obj = {
       'id': str(i),
       'values': list(map(float, row['Embedding'].split(','))),
       'metadata': {'text': row["Text"]},
       'sparse_values': sparse_vec
   }
   upsert_data.append(obj)

index.upsert(upsert_data)

