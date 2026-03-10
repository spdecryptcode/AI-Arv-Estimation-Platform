from meilisearch import Client
import os

MEILI_URL = os.getenv("MEILI_URL", "http://localhost:7700")
MEILI_MASTER_KEY = os.getenv("MEILI_MASTER_KEY", "masterKey")

meili_client = Client(MEILI_URL, MEILI_MASTER_KEY)

# ensure index exists, create if missing
try:
    index = meili_client.get_index("properties")
except Exception:
    index = meili_client.create_index("properties", {'primaryKey': 'id'})


def index_property(prop: dict):
    """Add or update a property document in MeiliSearch."""
    print(f"[meili] indexing document {prop}")
    try:
        result = index.add_documents([prop])
        print(f"[meili] add_documents result: {result}")
        return result
    except Exception as e:
        print(f"[meili] index_property error: {e}")
        raise


def delete_property(prop_id: str):
    """Remove a property document from the Meili index by its ID."""
    try:
        index.delete_document(prop_id)
    except Exception:
        # swallow errors, callers can ignore if index already absent
        pass


def search_properties(query: str, limit: int = 20):
    return index.search(query, {"limit": limit})
