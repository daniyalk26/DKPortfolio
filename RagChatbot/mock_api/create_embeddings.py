import pandas as pd
from sentence_transformers import SentenceTransformer

# Load the articles.csv file
df = pd.read_csv('embeddings.csv')

# Initialize the SentenceTransformer model
model = SentenceTransformer('Alibaba-NLP/gte-large-en-v1.5', trust_remote_code=True)

# Encode the text column to generate embeddings
embeddings = model.encode(df['Text'].tolist())

# Convert embeddings to a format suitable for saving in CSV
embeddings_str = [','.join(map(str, embedding)) for embedding in embeddings]

# Add the embeddings to the DataFrame
df['Embedding'] = embeddings_str

# Save the DataFrame back to articles.csv
df.to_csv('embeddings.csv', index=False)

print("Embeddings have been successfully added to the CSV file.")