# Products

Types:

```python
from henry_sdk.types import ProductRetrieveDetailsResponse, ProductSearchResponse
```

Methods:

- <code title="get /products/details">client.products.<a href="./src/henry_sdk/resources/products/products.py">retrieve_details</a>(\*\*<a href="src/henry_sdk/types/product_retrieve_details_params.py">params</a>) -> <a href="./src/henry_sdk/types/product_retrieve_details_response.py">ProductRetrieveDetailsResponse</a></code>
- <code title="post /products/search">client.products.<a href="./src/henry_sdk/resources/products/products.py">search</a>(\*\*<a href="src/henry_sdk/types/product_search_params.py">params</a>) -> <a href="./src/henry_sdk/types/product_search_response.py">ProductSearchResponse</a></code>

## VariantCheck

Types:

```python
from henry_sdk.types.products import VariantCheckCreateResponse, VariantCheckRetrieveStatusResponse
```

Methods:

- <code title="post /products/variant-check">client.products.variant_check.<a href="./src/henry_sdk/resources/products/variant_check.py">create</a>(\*\*<a href="src/henry_sdk/types/products/variant_check_create_params.py">params</a>) -> <a href="./src/henry_sdk/types/products/variant_check_create_response.py">VariantCheckCreateResponse</a></code>
- <code title="get /products/variant-check/{id}">client.products.variant_check.<a href="./src/henry_sdk/resources/products/variant_check.py">retrieve_status</a>(id) -> <a href="./src/henry_sdk/types/products/variant_check_retrieve_status_response.py">VariantCheckRetrieveStatusResponse</a></code>

# Cart

Types:

```python
from henry_sdk.types import CartCreateCheckoutResponse
```

Methods:

- <code title="post /cart/checkout">client.cart.<a href="./src/henry_sdk/resources/cart/cart.py">create_checkout</a>(\*\*<a href="src/henry_sdk/types/cart_create_checkout_params.py">params</a>) -> <a href="./src/henry_sdk/types/cart_create_checkout_response.py">CartCreateCheckoutResponse</a></code>

## Items

Types:

```python
from henry_sdk.types.cart import (
    ItemListResponse,
    ItemAddResponse,
    ItemClearResponse,
    ItemRemoveResponse,
)
```

Methods:

- <code title="get /cart/items">client.cart.items.<a href="./src/henry_sdk/resources/cart/items.py">list</a>() -> <a href="./src/henry_sdk/types/cart/item_list_response.py">ItemListResponse</a></code>
- <code title="post /cart/items">client.cart.items.<a href="./src/henry_sdk/resources/cart/items.py">add</a>(\*\*<a href="src/henry_sdk/types/cart/item_add_params.py">params</a>) -> <a href="./src/henry_sdk/types/cart/item_add_response.py">ItemAddResponse</a></code>
- <code title="delete /cart/items">client.cart.items.<a href="./src/henry_sdk/resources/cart/items.py">clear</a>() -> <a href="./src/henry_sdk/types/cart/item_clear_response.py">ItemClearResponse</a></code>
- <code title="delete /cart/items/{productId}">client.cart.items.<a href="./src/henry_sdk/resources/cart/items.py">remove</a>(product_id) -> <a href="./src/henry_sdk/types/cart/item_remove_response.py">ItemRemoveResponse</a></code>

# Checkout

## Session

Types:

```python
from henry_sdk.types.checkout import (
    SessionConfirmCheckoutResponse,
    SessionCreateQuoteResponse,
    SessionListProductsResponse,
    SessionRetrieveShippingInfoResponse,
)
```

Methods:

- <code title="post /checkout/session/confirm">client.checkout.session.<a href="./src/henry_sdk/resources/checkout/session.py">confirm_checkout</a>(\*\*<a href="src/henry_sdk/types/checkout/session_confirm_checkout_params.py">params</a>) -> <a href="./src/henry_sdk/types/checkout/session_confirm_checkout_response.py">SessionConfirmCheckoutResponse</a></code>
- <code title="post /checkout/session/quote">client.checkout.session.<a href="./src/henry_sdk/resources/checkout/session.py">create_quote</a>(\*\*<a href="src/henry_sdk/types/checkout/session_create_quote_params.py">params</a>) -> <a href="./src/henry_sdk/types/checkout/session_create_quote_response.py">SessionCreateQuoteResponse</a></code>
- <code title="get /checkout/session/products">client.checkout.session.<a href="./src/henry_sdk/resources/checkout/session.py">list_products</a>() -> <a href="./src/henry_sdk/types/checkout/session_list_products_response.py">SessionListProductsResponse</a></code>
- <code title="get /checkout/session/shipping">client.checkout.session.<a href="./src/henry_sdk/resources/checkout/session.py">retrieve_shipping_info</a>() -> <a href="./src/henry_sdk/types/checkout/session_retrieve_shipping_info_response.py">SessionRetrieveShippingInfoResponse</a></code>

# Orders

Types:

```python
from henry_sdk.types import OrderRetrieveStatusResponse
```

Methods:

- <code title="get /orders/{orderId}">client.orders.<a href="./src/henry_sdk/resources/orders.py">retrieve_status</a>(order_id) -> <a href="./src/henry_sdk/types/order_retrieve_status_response.py">OrderRetrieveStatusResponse</a></code>

# Wallet

Types:

```python
from henry_sdk.types import WalletCreateCardCollectionResponse
```

Methods:

- <code title="post /wallet/card-collect">client.wallet.<a href="./src/henry_sdk/resources/wallet.py">create_card_collection</a>(\*\*<a href="src/henry_sdk/types/wallet_create_card_collection_params.py">params</a>) -> <a href="./src/henry_sdk/types/wallet_create_card_collection_response.py">WalletCreateCardCollectionResponse</a></code>

# Merchants

Types:

```python
from henry_sdk.types import (
    MerchantCheckStatusResponse,
    MerchantGetShippingInfoResponse,
    MerchantListSupportedResponse,
)
```

Methods:

- <code title="get /merchants/{merchantDomain}/status">client.merchants.<a href="./src/henry_sdk/resources/merchants.py">check_status</a>(merchant_domain, \*\*<a href="src/henry_sdk/types/merchant_check_status_params.py">params</a>) -> <a href="./src/henry_sdk/types/merchant_check_status_response.py">MerchantCheckStatusResponse</a></code>
- <code title="get /merchants/shipping-info">client.merchants.<a href="./src/henry_sdk/resources/merchants.py">get_shipping_info</a>(\*\*<a href="src/henry_sdk/types/merchant_get_shipping_info_params.py">params</a>) -> <a href="./src/henry_sdk/types/merchant_get_shipping_info_response.py">MerchantGetShippingInfoResponse</a></code>
- <code title="get /merchants/list">client.merchants.<a href="./src/henry_sdk/resources/merchants.py">list_supported</a>(\*\*<a href="src/henry_sdk/types/merchant_list_supported_params.py">params</a>) -> <a href="./src/henry_sdk/types/merchant_list_supported_response.py">MerchantListSupportedResponse</a></code>
