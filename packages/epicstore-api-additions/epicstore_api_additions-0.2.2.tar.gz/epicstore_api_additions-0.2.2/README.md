# epicstore_api_additions

[![Current pypi version](https://img.shields.io/pypi/v/epicstore-api-additions.svg)](https://pypi.org/project/epicstore-api-additions/)
[![Supported py versions](https://img.shields.io/pypi/pyversions/epicstore-api-additions.svg)](https://pypi.org/project/epicstore-api-additions/)
[![Downloads](https://pepy.tech/badge/epicstore-api-additions)](https://pypi.org/project/epicstore-api-additions/)

An unofficial library to work with Epic Games Store Web API.
**The library works with `cloudscraper` under the hood to battle the anti-bot protections, please be careful with the amount of requests you do, as this is not a silver bullet.**

## About This Fork

This is a customized fork of the original `epicstore_api` library with additional features and improvements:

- Added `get_store_config()` method to retrieve store configuration for products by sandbox ID
- Added `get_product_by_id()` method to retrieve product details by product ID
- Added `get_product_offer_by_id()` method to retrieve offer details by product ID and offer ID
- Added `get_product_ipv4()` method to retrieve product details using IPv4 endpoint
- Added `get_catalog_offer()` method to retrieve catalog offer details with flexible sha256Hash support
- Implemented support for persisted GraphQL queries with hash caching mechanism
- Added configurable hash endpoint for fetching GraphQL operation hashes
- Enhanced performance with caching for sha256Hash values
- Improved error handling and flexibility for API interactions
- sha256Hash can be provided at call time for persisted queries, avoiding hardcoding in the package
- No hardcoded sha256Hash values - all hashes must be provided explicitly or via hash_endpoint

## Installing

**Python 3.7 or higher is required**

To install the library you can just run the following command:

``` sh
# Linux/macOS
python3 -m pip install -U epicstore_api_additions

# Windows
py -3 -m pip install -U epicstore_api_additions
```


### Quick Example

``` py
api = EpicGamesStoreAPI()
namespace, slug = next(iter(api.get_product_mapping().items()))
first_product = api.get_product(slug)
offers = [
    OfferData(page['namespace'], page['offer']['id'])
    for page in first_product['pages']
    if page.get('offer') and 'id' in page['offer']
]
offers_data = api.get_offers_data(*offers)
for offer_data in offers_data:
    data = offer_data['data']['Catalog']['catalogOffer']
    developer_name = ''
    for custom_attribute in data['customAttributes']:
        if custom_attribute['key'] == 'developerName':
            developer_name = custom_attribute['value']
    print('Offer ID:', data['id'], '\nDeveloper Name:', developer_name)
```

### New Feature: Get Store Configuration

```python
from epicstore_api import EpicGamesStoreAPI

# Initialize API
api = EpicGamesStoreAPI(locale="zh-CN")

# Get store configuration for a product by sandbox ID
# Option 1: Provide sha256Hash explicitly
sandbox_id = "b4bb52a95d0b43d9af543c6ec3c54e04"  # Example sandbox ID
sha256_hash = "f51a14bfd8e8969386e70f7c734c2671d9f61833021174e44723ddda9881739e"
config = api.get_store_config(sandbox_id, sha256_hash=sha256_hash)
print(config)

# Option 2: Configure hash_endpoint to fetch hash automatically
# api = EpicGamesStoreAPI(locale="zh-CN", hash_endpoint="https://your-hash-service.com/api/hash")
# config = api.get_store_config(sandbox_id)  # Will fetch hash from endpoint
```

### New Feature: Get Product by ID

```python
from epicstore_api import EpicGamesStoreAPI

# Initialize API
api = EpicGamesStoreAPI(locale="zh-CN", country="TW")

# Get product details by product ID
product_id = "3ac65ef5cdf44b8084fcac818002635f"  # Example product ID
product = api.get_product_by_id(product_id)
print(product)
```

### New Feature: Get Product Offer by ID

```python
from epicstore_api import EpicGamesStoreAPI

# Initialize API
api = EpicGamesStoreAPI(locale="zh-CN", country="TW")

# Get offer details by product ID and offer ID
product_id = "3ac65ef5cdf44b8084fcac818002635f"  # Example product ID
offer_id = "cb49140c3c11429589ab22fd75c41504"  # Example offer ID
offer = api.get_product_offer_by_id(product_id, offer_id)
print(offer)
```

### New Feature: Get Product by Slug (IPv4 Endpoint)

```python
from epicstore_api import EpicGamesStoreAPI

# Initialize API
api = EpicGamesStoreAPI(locale="zh-CN")

# Get product details using IPv4 endpoint
slug = "fall-guys"  # Product slug
product = api.get_product_ipv4(slug)
print(product)
# Returns detailed product information including pages, namespace, theme, etc.
```

### New Feature: Get Catalog Offer

```python
from epicstore_api import EpicGamesStoreAPI

# Initialize API
api = EpicGamesStoreAPI(locale="zh-CN", country="TW")

# Get catalog offer details
# Option 1: Provide sha256Hash explicitly (recommended)
offer = api.get_catalog_offer(
    offer_id="f506d29d55bb4c72b8d57fd9857b2be4",
    sandbox_id="94cec4802e954a6c9579e29e8b817f3a",
    sha256_hash="abafd6e0aa80535c43676f533f0283c7f5214a59e9fae6ebfb37bed1b1bb2e9b"
)

# Option 2: Let the method use default hash (will try cache/endpoint first)
offer = api.get_catalog_offer(
    offer_id="f506d29d55bb4c72b8d57fd9857b2be4",
    sandbox_id="94cec4802e954a6c9579e29e8b817f3a"
)
print(offer)
```

The `sha256_hash` parameter allows you to provide the hash at call time, avoiding hardcoding it in the package. If not provided, the method will try to get it from cache or configured hash_endpoint. If hash_endpoint is not configured, you must provide the sha256_hash parameter explicitly.

You can find more examples in the examples directory.

### Contributing
Feel free to contribute by creating PRs and sending your issues

## Links
* [Documentation](https://epicstore-api.readthedocs.io/en/latest/)

## License
MIT