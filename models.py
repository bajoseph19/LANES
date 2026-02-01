"""
LANES - Database Models
Extended models for Holistic Market widget integration
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100))
    address = db.Column(db.String(500))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    recipes = db.relationship('Recipe', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Recipe(db.Model):
    """Recipe model to store parsed recipes"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(200))
    pcp_id = db.Column(db.Integer, db.ForeignKey('partner_content_provider.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ingredients = db.relationship('Ingredient', backref='recipe', lazy=True, cascade='all, delete-orphan')


class Ingredient(db.Model):
    """Ingredient model to store parsed ingredients"""
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.String(50))
    unit = db.Column(db.String(50))
    item = db.Column(db.String(200))
    in_cart = db.Column(db.Boolean, default=True)
    amazon_fresh_product_id = db.Column(db.Integer, db.ForeignKey('amazon_fresh_product.id'))
    amazon_fresh_product = db.relationship('AmazonFreshProduct', backref='ingredients')


class PartnerContentProvider(db.Model):
    """Partner Content Provider (PCP) - recipe websites that embed the widget"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    domain = db.Column(db.String(255), unique=True, nullable=False)
    api_key = db.Column(db.String(64), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    schemas = db.relationship('PCPSchema', backref='pcp', lazy=True)
    recipes = db.relationship('Recipe', backref='pcp', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'domain': self.domain,
            'is_active': self.is_active
        }


class PCPSchema(db.Model):
    """Schema definitions for web scraping partner content provider pages"""
    id = db.Column(db.Integer, primary_key=True)
    pcp_id = db.Column(db.Integer, db.ForeignKey('partner_content_provider.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    selector_type = db.Column(db.String(50), default='css')  # css, xpath, json-ld
    ingredient_selector = db.Column(db.String(500))
    title_selector = db.Column(db.String(500))
    image_selector = db.Column(db.String(500))
    url_pattern = db.Column(db.String(500))  # regex pattern for matching recipe URLs
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'pcp_id': self.pcp_id,
            'name': self.name,
            'selector_type': self.selector_type,
            'ingredient_selector': self.ingredient_selector,
            'title_selector': self.title_selector,
            'url_pattern': self.url_pattern
        }


class LocalStorageCache(db.Model):
    """Local storage cache for recipe page information"""
    id = db.Column(db.Integer, primary_key=True)
    url_hash = db.Column(db.String(64), unique=True, nullable=False)  # SHA256 of URL
    url = db.Column(db.String(500), nullable=False)
    pcp_id = db.Column(db.Integer, db.ForeignKey('partner_content_provider.id'))
    recipe_data = db.Column(db.Text)  # JSON serialized recipe data
    amazon_fresh_data = db.Column(db.Text)  # JSON serialized Amazon Fresh product data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

    def get_recipe_data(self):
        if self.recipe_data:
            return json.loads(self.recipe_data)
        return None

    def set_recipe_data(self, data):
        self.recipe_data = json.dumps(data)

    def get_amazon_fresh_data(self):
        if self.amazon_fresh_data:
            return json.loads(self.amazon_fresh_data)
        return None

    def set_amazon_fresh_data(self, data):
        self.amazon_fresh_data = json.dumps(data)

    def is_expired(self):
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False


class AmazonFreshProduct(db.Model):
    """Amazon Fresh product data"""
    id = db.Column(db.Integer, primary_key=True)
    asin = db.Column(db.String(20), unique=True)  # Amazon Standard Identification Number
    name = db.Column(db.String(500), nullable=False)
    price = db.Column(db.Float)
    unit_price = db.Column(db.String(50))  # e.g., "$0.25/oz"
    image_url = db.Column(db.String(500))
    category = db.Column(db.String(100))
    in_stock = db.Column(db.Boolean, default=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'asin': self.asin,
            'name': self.name,
            'price': self.price,
            'unit_price': self.unit_price,
            'image_url': self.image_url,
            'category': self.category,
            'in_stock': self.in_stock
        }


class Order(db.Model):
    """Order model for checkout flow"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, submitted, processing, shipped, delivered

    # Shipping information
    shipping_name = db.Column(db.String(100))
    shipping_email = db.Column(db.String(120))
    shipping_address = db.Column(db.String(500))
    shipping_phone = db.Column(db.String(20))

    # Payment
    payment_method = db.Column(db.String(50))  # credit_card, amazon_pay, etc.
    subtotal = db.Column(db.Float, default=0.0)
    tax = db.Column(db.Float, default=0.0)
    shipping_cost = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)

    # Fulfillment
    fulfillment_partner = db.Column(db.String(50), default='amazon_fresh')
    external_order_id = db.Column(db.String(100))  # Order ID from Amazon Fresh

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime)
    shipped_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)

    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'status': self.status,
            'total': self.total,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'items': [item.to_dict() for item in self.items]
        }


class OrderItem(db.Model):
    """Individual items in an order"""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'))
    amazon_fresh_product_id = db.Column(db.Integer, db.ForeignKey('amazon_fresh_product.id'))

    ingredient_text = db.Column(db.String(500))  # Original ingredient text
    product_name = db.Column(db.String(500))  # Amazon Fresh product name
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, default=0.0)

    ingredient = db.relationship('Ingredient', backref='order_items')
    amazon_fresh_product = db.relationship('AmazonFreshProduct', backref='order_items')

    def to_dict(self):
        return {
            'id': self.id,
            'ingredient_text': self.ingredient_text,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'price': self.price
        }
