from opensearchpy import OpenSearch

# Initialize the OpenSearch client
client = OpenSearch(
    hosts=[{'host': 'localhost', 'port': 9200}],
    use_ssl=False,
    verify_certs=False,
    ssl_show_warn=False
)

# Specify the name of the index to be deleted
index_name = "payactiv-chatbot-index"

# Delete the index
response = client.indices.delete(index=index_name)
print(response)
