from elasticsearch import Elasticsearch
from inception_db_connect.settings_db_connect import get_db_connect_setting
from inception_db_connect.helper import mask_url


# Get settings
db_connect_setting = get_db_connect_setting()
print(
    f"📡 Connecting to Elasticsearch at: {mask_url(db_connect_setting.elasticsearch_url)}"
)

# Connect to ES
es = Elasticsearch(db_connect_setting.elasticsearch_url, verify_certs=db_connect_setting.elasticsearch_verify_certs)

# ✅ Confirm connection
if es.ping():
    print("✅ Successfully connected to Elasticsearch!")
else:
    print("❌ Failed to connect to Elasticsearch.")
    raise ConnectionError("Could not connect to Elasticsearch.")


def get_es_client_on_demand():
    return es


def get_es_client():
    es_client = Elasticsearch(db_connect_setting.elasticsearch_url, verify_certs=db_connect_setting.elasticsearch_verify_certs)
    try:
        yield es_client
    finally:
        es_client.close()


async def index_document(index_name: str, document_id: str, body: dict):
    response = es.index(index=index_name, id=document_id, document=body)
    print(f"✅ Successfully indexed document into Elasticsearch: {document_id}")
    return response


async def search_es_documents(index_name: str, query: dict):
    response = es.search(index=index_name, body=query)
    print(f"✅ Successfully searched Elasticsearch: {response}")
    return response
