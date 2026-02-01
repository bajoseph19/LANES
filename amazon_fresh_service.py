"""
Amazon Fresh Integration Service
Handles product matching, pricing, and order submission to Amazon Fresh

Note: This is a mock implementation. In production, this would integrate
with Amazon's Product Advertising API and Amazon Fresh delivery API.
"""
import re
import random
import string
from datetime import datetime
from difflib import SequenceMatcher


class AmazonFreshService:
    """
    Service for integrating with Amazon Fresh

    Implements the following from process flows:
    - "Amazon Fresh product data" retrieval
    - "Amazon Fresh Data Package" creation
    - "Order received" submission
    - "Process Order and Ship to Customer" tracking
    """

    # Mock product database (in production, this would query Amazon's API)
    MOCK_PRODUCTS = {
        'milk': {'asin': 'B001234567', 'name': 'Organic Whole Milk, 1 Gallon', 'price': 5.99, 'category': 'Dairy'},
        'eggs': {'asin': 'B001234568', 'name': 'Large Brown Eggs, 12 count', 'price': 4.49, 'category': 'Dairy'},
        'butter': {'asin': 'B001234569', 'name': 'Unsalted Butter, 1 lb', 'price': 4.99, 'category': 'Dairy'},
        'flour': {'asin': 'B001234570', 'name': 'All-Purpose Flour, 5 lb', 'price': 3.99, 'category': 'Baking'},
        'sugar': {'asin': 'B001234571', 'name': 'Granulated Sugar, 4 lb', 'price': 3.49, 'category': 'Baking'},
        'salt': {'asin': 'B001234572', 'name': 'Sea Salt, 26 oz', 'price': 2.99, 'category': 'Spices'},
        'pepper': {'asin': 'B001234573', 'name': 'Ground Black Pepper, 4 oz', 'price': 4.99, 'category': 'Spices'},
        'olive oil': {'asin': 'B001234574', 'name': 'Extra Virgin Olive Oil, 16.9 oz', 'price': 8.99, 'category': 'Oils'},
        'garlic': {'asin': 'B001234575', 'name': 'Fresh Garlic, 3 count', 'price': 1.99, 'category': 'Produce'},
        'onion': {'asin': 'B001234576', 'name': 'Yellow Onions, 3 lb bag', 'price': 2.99, 'category': 'Produce'},
        'chicken': {'asin': 'B001234577', 'name': 'Boneless Chicken Breast, 1.5 lb', 'price': 9.99, 'category': 'Meat'},
        'beef': {'asin': 'B001234578', 'name': 'Ground Beef 80/20, 1 lb', 'price': 6.99, 'category': 'Meat'},
        'rice': {'asin': 'B001234579', 'name': 'Long Grain White Rice, 2 lb', 'price': 3.49, 'category': 'Grains'},
        'pasta': {'asin': 'B001234580', 'name': 'Spaghetti Pasta, 16 oz', 'price': 1.99, 'category': 'Grains'},
        'tomato': {'asin': 'B001234581', 'name': 'Roma Tomatoes, 1 lb', 'price': 2.49, 'category': 'Produce'},
        'cheese': {'asin': 'B001234582', 'name': 'Shredded Mozzarella, 8 oz', 'price': 3.99, 'category': 'Dairy'},
        'cream': {'asin': 'B001234583', 'name': 'Heavy Whipping Cream, 16 oz', 'price': 4.49, 'category': 'Dairy'},
        'mushroom': {'asin': 'B001234584', 'name': 'White Mushrooms, 8 oz', 'price': 2.99, 'category': 'Produce'},
        'spinach': {'asin': 'B001234585', 'name': 'Baby Spinach, 5 oz', 'price': 3.99, 'category': 'Produce'},
        'lemon': {'asin': 'B001234586', 'name': 'Fresh Lemons, 2 lb bag', 'price': 3.49, 'category': 'Produce'},
        'bread': {'asin': 'B001234587', 'name': 'Whole Wheat Bread, 20 oz', 'price': 3.29, 'category': 'Bakery'},
        'parsley': {'asin': 'B001234588', 'name': 'Fresh Parsley, 1 bunch', 'price': 1.49, 'category': 'Produce'},
        'basil': {'asin': 'B001234589', 'name': 'Fresh Basil, 0.75 oz', 'price': 2.49, 'category': 'Produce'},
        'oregano': {'asin': 'B001234590', 'name': 'Dried Oregano, 0.75 oz', 'price': 3.49, 'category': 'Spices'},
        'thyme': {'asin': 'B001234591', 'name': 'Fresh Thyme, 0.66 oz', 'price': 2.99, 'category': 'Produce'},
        'bacon': {'asin': 'B001234592', 'name': 'Applewood Smoked Bacon, 16 oz', 'price': 7.99, 'category': 'Meat'},
        'sour cream': {'asin': 'B001234593', 'name': 'Sour Cream, 16 oz', 'price': 2.99, 'category': 'Dairy'},
        'cream cheese': {'asin': 'B001234594', 'name': 'Cream Cheese, 8 oz', 'price': 2.49, 'category': 'Dairy'},
        'mayo': {'asin': 'B001234595', 'name': 'Mayonnaise, 30 oz', 'price': 4.99, 'category': 'Condiments'},
        'mustard': {'asin': 'B001234596', 'name': 'Yellow Mustard, 14 oz', 'price': 2.49, 'category': 'Condiments'},
    }

    def __init__(self, db=None, AmazonFreshProduct=None):
        self.db = db
        self.AmazonFreshProduct = AmazonFreshProduct

    def match_ingredient_to_product(self, ingredient_text):
        """
        Match an ingredient to an Amazon Fresh product

        Uses fuzzy matching to find the best product match
        """
        ingredient_lower = ingredient_text.lower()

        # First try exact keyword match
        for keyword, product in self.MOCK_PRODUCTS.items():
            if keyword in ingredient_lower:
                return {
                    'matched': True,
                    'confidence': 0.9,
                    'product': product,
                    'original_ingredient': ingredient_text
                }

        # Fuzzy match if no exact match
        best_match = None
        best_score = 0

        for keyword, product in self.MOCK_PRODUCTS.items():
            # Check similarity
            score = SequenceMatcher(None, ingredient_lower, keyword).ratio()
            if score > best_score and score > 0.4:
                best_score = score
                best_match = product

        if best_match:
            return {
                'matched': True,
                'confidence': best_score,
                'product': best_match,
                'original_ingredient': ingredient_text
            }

        # No match found - return generic item
        return {
            'matched': False,
            'confidence': 0,
            'product': {
                'asin': None,
                'name': ingredient_text,
                'price': 5.00,  # Default price
                'category': 'Other'
            },
            'original_ingredient': ingredient_text
        }

    def get_amazon_fresh_data_package(self, ingredients):
        """
        Create an Amazon Fresh Data Package from ingredients

        Implements: "Amazon Fresh Data Package" in process flow
        """
        products = []
        total_price = 0

        for ingredient in ingredients:
            if isinstance(ingredient, str):
                ingredient_text = ingredient
            else:
                ingredient_text = ingredient.get('text', str(ingredient))

            match = self.match_ingredient_to_product(ingredient_text)
            product_data = {
                'ingredient_text': ingredient_text,
                'product': match['product'],
                'matched': match['matched'],
                'confidence': match['confidence'],
                'quantity': 1,
                'subtotal': match['product']['price']
            }
            products.append(product_data)
            total_price += match['product']['price']

        return {
            'products': products,
            'subtotal': round(total_price, 2),
            'tax': round(total_price * 0.08, 2),  # 8% tax
            'delivery_fee': 4.99 if total_price < 35 else 0,  # Free delivery over $35
            'total': round(total_price * 1.08 + (4.99 if total_price < 35 else 0), 2),
            'item_count': len(products),
            'generated_at': datetime.utcnow().isoformat()
        }

    def create_or_update_product(self, product_data):
        """Save or update product in database"""
        if not self.db or not self.AmazonFreshProduct:
            return None

        product = self.AmazonFreshProduct.query.filter_by(
            asin=product_data.get('asin')
        ).first()

        if not product:
            product = self.AmazonFreshProduct(
                asin=product_data.get('asin'),
                name=product_data['name'],
                price=product_data.get('price'),
                category=product_data.get('category'),
                in_stock=True
            )
            self.db.session.add(product)
        else:
            product.name = product_data['name']
            product.price = product_data.get('price')
            product.category = product_data.get('category')

        self.db.session.commit()
        return product

    def submit_order(self, order_data):
        """
        Submit order to Amazon Fresh

        Implements: "Order received" and "Process Order and Ship to Customer"

        In production, this would call Amazon Fresh's order API
        """
        # Generate mock external order ID
        external_order_id = 'AF-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

        return {
            'success': True,
            'external_order_id': external_order_id,
            'status': 'submitted',
            'estimated_delivery': '2-4 hours',
            'message': 'Order submitted to Amazon Fresh successfully',
            'tracking_url': f'https://www.amazon.com/gp/your-account/order-details?orderID={external_order_id}'
        }

    def check_order_status(self, external_order_id):
        """
        Check order status from Amazon Fresh

        In production, this would query Amazon Fresh's order status API
        """
        # Mock order statuses
        statuses = ['processing', 'picked', 'out_for_delivery', 'delivered']
        return {
            'external_order_id': external_order_id,
            'status': random.choice(statuses),
            'last_updated': datetime.utcnow().isoformat()
        }


class FulfillmentService:
    """
    Service for managing order fulfillment across multiple providers

    Currently supports Amazon Fresh, extensible for Instacart, etc.
    """

    PROVIDERS = {
        'amazon_fresh': AmazonFreshService,
        # Future: 'instacart': InstacartService,
    }

    def __init__(self, db=None, AmazonFreshProduct=None):
        self.db = db
        self.AmazonFreshProduct = AmazonFreshProduct
        self._services = {}

    def get_service(self, provider='amazon_fresh'):
        """Get fulfillment service for a provider"""
        if provider not in self._services:
            service_class = self.PROVIDERS.get(provider)
            if service_class:
                self._services[provider] = service_class(self.db, self.AmazonFreshProduct)
            else:
                raise ValueError(f"Unknown fulfillment provider: {provider}")
        return self._services[provider]

    def get_available_providers(self):
        """Get list of available fulfillment providers"""
        return list(self.PROVIDERS.keys())
