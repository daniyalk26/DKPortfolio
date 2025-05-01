from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
from sentence_transformers import SentenceTransformer
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

pinecone_key = os.getenv('PINECONE_API_KEY')
pc = Pinecone(api_key=pinecone_key)
index_name = "payactiv-chatbot-index"

# Initialize the SentenceTransformer model
model = SentenceTransformer('Alibaba-NLP/gte-large-en-v1.5', trust_remote_code=True)

# Dictionary with texts and their associated classes
texts_to_embed = {
    "Which account do you want to transfer from": "account",
    "Which account do you want to transfer to": "account",
    "How much do you want to transfer": "transfer_amount",
    "Please confirm the transfer": "confirm_transfer",
    "Do you confirm the transfer": "confirm_transfer",
    "Which account balance would you like to check": "account",
    "Please specify which account you would like to check the balance for": "account"
}

# Convert dictionary to DataFrame
df = pd.DataFrame(list(texts_to_embed.items()), columns=['Text', 'Class'])

# Encode the text column to generate embeddings
embeddings = model.encode(df['Text'].tolist())

# Add embeddings to the DataFrame
df['Embedding'] = embeddings.tolist()

index = pc.Index(index_name)

upsert_data = [
    (str(i), row['Embedding'], {'text': row['Text'], 'class': row['Class']})
    for i, row in df.iterrows()
]

index.upsert(vectors=upsert_data, namespace="dynamic-qa")


