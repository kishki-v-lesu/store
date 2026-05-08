import logging
from typing import Optional

from elasticsearch import AsyncElasticsearch

from app.core.config import settings

logger = logging.getLogger(__name__)

es_client: Optional[AsyncElasticsearch] = None

PRODUCT_INDEX = "products"


async def get_es_client() -> AsyncElasticsearch:
    global es_client
    if es_client is None:
        es_client = AsyncElasticsearch([settings.ELASTICSEARCH_URL])
    return es_client


async def create_products_index():
    client = await get_es_client()
    
    if await client.indices.exists(index=PRODUCT_INDEX):
        return
    
    await client.indices.create(
        index=PRODUCT_INDEX,
        body={
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "product_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "asciifolding"]
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "text", "analyzer": "product_analyzer"},
                    "description": {"type": "text", "analyzer": "product_analyzer"},
                    "price": {"type": "float"},
                    "category_id": {"type": "integer"},
                    "sku": {"type": "keyword"},
                    "stock_quantity": {"type": "integer"},
                    "is_active": {"type": "boolean"},
                }
            }
        }
    )
    logger.info(f"Created Elasticsearch index: {PRODUCT_INDEX}")


async def index_product(product_id: int, product_data: dict):
    client = await get_es_client()
    await client.index(
        index=PRODUCT_INDEX,
        id=str(product_id),
        body=product_data,
        refresh=True,
    )
    logger.info(f"Indexed product {product_id} to Elasticsearch")


async def delete_product_from_index(product_id: int):
    client = await get_es_client()
    try:
        await client.delete(index=PRODUCT_INDEX, id=str(product_id), refresh=True)
    except Exception:
        pass


async def search_products(query: str, category_id: Optional[int] = None, page: int = 1, per_page: int = 20):
    client = await get_es_client()
    
    must_clauses = [
        {"match": {"name": {"query": query, "fuzziness": "AUTO"}}},
    ]
    
    if category_id:
        must_clauses.append({"term": {"category_id": category_id}})
    
    body = {
        "query": {
            "bool": {
                "must": must_clauses,
                "filter": [{"term": {"is_active": True}}]
            }
        },
        "from": (page - 1) * per_page,
        "size": per_page,
    }
    
    result = await client.search(index=PRODUCT_INDEX, body=body)
    
    hits = result["hits"]["hits"]
    total = result["hits"]["total"]["value"]
    
    products = []
    for hit in hits:
        product = hit["_source"]
        product["id"] = int(hit["_id"])
        products.append(product)
    
    return products, total


async def close_es_client():
    global es_client
    if es_client:
        await es_client.close()
        es_client = None