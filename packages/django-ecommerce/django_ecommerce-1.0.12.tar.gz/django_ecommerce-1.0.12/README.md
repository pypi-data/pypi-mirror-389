# Django E-commerce

This Django E-commerce app empowers online retail businesses with robust features for managing products, categories, and
orders. It includes versatile functionalities such as discount management, stock tracking, and flexible settings
configuration to streamline the end-to-end E-commerce process.

## Installation

* Install this package using pip

```bash
pip install django-ecommerce
```

* Add **django_ecommerce** to your **INSTALLED_APPS** setting like this

```python
INSTALLED_APPS = [
    ...,
    "django_ecommerce",
]
```

* Migrate your database

```bash
python manage.py migrate
```

## Configuration

In the Django settings file, customize the available currencies for your E-commerce platform by modifying the
`ECOMMERCE_AVAILABLE_CURRENCIES` list. Set the default currency using the `ECOMMERCE_DEFAULT_CURRENCY` variable,
and tailor the displayed fields in the shipping administration interface with the `ECOMMERCE_SHIPPING_ADMIN_FIELDS`.

```python
ECOMMERCE_AVAILABLE_CURRENCIES = [
    ('EUR', 'EUR'),
    ('USD', 'USD'),
]
ECOMMERCE_DEFAULT_CURRENCY = 'EUR'
ECOMMERCE_SHIPPING_ADMIN_FIELDS = ['full_name', 'address', 'phone', 'city', 'shipping_amount', 'remark']
```

## Usage

To seamlessly integrate an ecommerce system into your Django application, it is recommended to leverage the utility 
functions provided by django_ecommerce.utils. These functions, including adding to cart, removing from cart, and 
creating orders, offer a convenient and robust solution for managing various ecommerce interactions within your application.

Here is a list of utility functions from django_ecommerce.utils with concise explanations for each

* **chunks(queryset, chunk_size)**
  - Divides a given queryset into smaller chunks for more efficient processing.

* **similar_products(product, limit=4)**
  - Finds and returns a specified number of products similar to the given product, excluding the original.

* **variant_availability(variant: ProductVariant, request) -> int**
  - Determines the availability of a product variant by subtracting the quantity in the user's cart from the total available quantity.

* **money(amount: float, currency: str = None) -> Money**
  - Generates a Money instance with the specified amount and currency. Uses the default currency from Django settings if available.

* **get_shipping_data(amount: Money) -> dict**
  - Retrieves shipping-related data based on the total order amount, considering factors like free shipping eligibility and shipping cost.

* **get_cart(request)**
  - Retrieves information about the user's shopping cart, including items, total cost, quantity, and shipping details.

* **remove_from_cart(request, variant_id: int) -> dict**
  - Removes a specified product variant from the user's shopping cart.

* **add_to_cart(request, variant_id: int, quantity: int = 1) -> dict**
  - Adds a specified quantity of a product variant to the user's shopping cart, considering stock availability.

* **create_order(request, email: str = None, full_name: str = None, ...) -> dict**
  - Creates an order based on the user's shopping cart and specified details, including customer information and a custom callback function.

* **get_cities() -> set**
  - Retrieves a set of city names from the database.

* **get_countries() -> set**
  - Retrieves a set of country names from the database.

* **find_product_by_slug(slug: str) -> Product | None**
  - Finds and returns a product based on its slug. Returns None if the product does not exist.

* **find_category_by_slug(slug: str) -> Category | None**
  - Finds and returns a category based on its slug. Returns None if the category does not exist.

* **find_order_by_code(code: str) -> Order | None**
  - Finds and returns an order based on its unique code. Returns None if the order does not exist.