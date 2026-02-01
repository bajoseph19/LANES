"""
LANES - Recipe Parser Web Application
Main Flask application for converting recipe URLs into ingredient shopping carts
with Holistic Market widget integration and Amazon Fresh checkout
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from datetime import datetime

from models import (
    db, User, Recipe, Ingredient, PartnerContentProvider,
    PCPSchema, LocalStorageCache, AmazonFreshProduct, Order, OrderItem
)
from recipe_parser import RecipeParser
from widget_service import WidgetService, LocalStorageService, SchemaService
from amazon_fresh_service import AmazonFreshService, FulfillmentService
from checkout_service import CheckoutService, EmailService

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lanes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize services
parser = RecipeParser()
amazon_fresh_service = AmazonFreshService()
email_service = EmailService(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Initialize services that need db
def get_checkout_service():
    return CheckoutService(db, Order, OrderItem, amazon_fresh_service)


def get_local_storage_service():
    return LocalStorageService(db, LocalStorageCache)


def get_schema_service():
    return SchemaService(db, PCPSchema)


# ============================================================================
# Authentication Routes
# ============================================================================

@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')

        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('signup.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('signup.html')

        user = User(email=email, name=name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash('Account created successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))


# ============================================================================
# Dashboard & Recipe Routes
# ============================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard showing saved recipes"""
    recipes = Recipe.query.filter_by(user_id=current_user.id).order_by(Recipe.created_at.desc()).all()
    return render_template('dashboard.html', recipes=recipes)


@app.route('/parse-recipe', methods=['GET', 'POST'])
@login_required
def parse_recipe():
    """Parse a recipe from URL"""
    if request.method == 'POST':
        url = request.form.get('url')

        if not url:
            flash('Recipe URL is required', 'error')
            return render_template('parse_recipe.html')

        try:
            # Check local storage cache first (per process flow)
            local_storage = get_local_storage_service()
            cached = local_storage.get_cached_data(url)

            if cached and cached.get('recipe_data'):
                ingredients = cached['recipe_data'].get('ingredients', [])
                title = cached['recipe_data'].get('title', 'Cached Recipe')
            else:
                # Parse the recipe using web scraper
                ingredients = parser.get_ingredients(url)

                if not ingredients:
                    flash('Could not extract ingredients from this URL.', 'warning')
                    return render_template('parse_recipe.html')

                # Extract title from URL
                from urllib.parse import urlparse
                parsed_url = urlparse(url)
                path_parts = [p for p in parsed_url.path.split('/') if p]
                if path_parts:
                    title = path_parts[-1].replace('-', ' ').replace('_', ' ').title()
                else:
                    title = f"Recipe from {parsed_url.netloc}"

                if len(title) > 100:
                    title = title[:97] + '...'

                # Cache the recipe data
                local_storage.cache_recipe_data(url, {
                    'ingredients': ingredients,
                    'title': title,
                    'url': url
                })

            # Save recipe to database
            recipe = Recipe(user_id=current_user.id, url=url, title=title)
            db.session.add(recipe)
            db.session.flush()

            for ing_text in ingredients:
                ingredient = Ingredient(
                    recipe_id=recipe.id,
                    text=ing_text,
                    in_cart=True
                )
                db.session.add(ingredient)

            db.session.commit()

            flash(f'Successfully extracted {len(ingredients)} ingredients!', 'success')
            return redirect(url_for('view_recipe', recipe_id=recipe.id))

        except Exception as e:
            flash(f'Error parsing recipe: {str(e)}', 'error')
            return render_template('parse_recipe.html')

    return render_template('parse_recipe.html')


@app.route('/recipe/<int:recipe_id>')
@login_required
def view_recipe(recipe_id):
    """View a specific recipe and its ingredients"""
    recipe = Recipe.query.get_or_404(recipe_id)

    if recipe.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))

    # Get Amazon Fresh pricing for ingredients
    ingredient_texts = [ing.text for ing in recipe.ingredients]
    amazon_data = amazon_fresh_service.get_amazon_fresh_data_package(ingredient_texts)

    return render_template('recipe.html', recipe=recipe, amazon_data=amazon_data)


# ============================================================================
# Cart Routes
# ============================================================================

@app.route('/cart')
@login_required
def cart():
    """View shopping cart with all ingredients from saved recipes"""
    recipes = Recipe.query.filter_by(user_id=current_user.id).all()

    cart_items = []
    for recipe in recipes:
        for ingredient in recipe.ingredients:
            if ingredient.in_cart:
                cart_items.append({
                    'id': ingredient.id,
                    'text': ingredient.text,
                    'recipe_url': recipe.url,
                    'recipe_id': recipe.id,
                    'ingredient': ingredient
                })

    # Get Amazon Fresh data package for cart
    if cart_items:
        ingredient_texts = [item['text'] for item in cart_items]
        amazon_data = amazon_fresh_service.get_amazon_fresh_data_package(ingredient_texts)
    else:
        amazon_data = None

    return render_template('cart.html', cart_items=cart_items, amazon_data=amazon_data)


# ============================================================================
# Checkout Routes (Process Flow: User Checkout)
# ============================================================================

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """
    Checkout page - User provides checkout information

    Process Flow Step: Widget prompts user for checkout information
    User provides: Email, Name, Address, Phone number, Payment Method
    """
    # Get cart items
    recipes = Recipe.query.filter_by(user_id=current_user.id).all()
    cart_items = []
    for recipe in recipes:
        for ingredient in recipe.ingredients:
            if ingredient.in_cart:
                cart_items.append(ingredient)

    if not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('cart'))

    # Get Amazon Fresh data package
    ingredient_texts = [item.text for item in cart_items]
    amazon_data = amazon_fresh_service.get_amazon_fresh_data_package(ingredient_texts)

    if request.method == 'POST':
        # Collect checkout information
        checkout_data = {
            'shipping_name': request.form.get('name'),
            'shipping_email': request.form.get('email'),
            'shipping_address': request.form.get('address'),
            'shipping_phone': request.form.get('phone'),
            'payment_method': request.form.get('payment_method', 'credit_card')
        }

        # Validate required fields
        if not all([checkout_data['shipping_name'], checkout_data['shipping_email'],
                    checkout_data['shipping_address'], checkout_data['shipping_phone']]):
            flash('Please fill in all required fields', 'error')
            return render_template('checkout.html',
                                   cart_items=cart_items,
                                   amazon_data=amazon_data,
                                   user=current_user)

        # Create order
        checkout_service = get_checkout_service()
        order, order_amazon_data = checkout_service.create_order(
            current_user, checkout_data, cart_items
        )

        # Submit order to Amazon Fresh
        result = checkout_service.submit_order(order)

        if result['success']:
            # Send confirmation email
            email_service.send_order_confirmation(order, checkout_data['shipping_email'])

            # Clear cart items
            for item in cart_items:
                item.in_cart = False
            db.session.commit()

            flash('Order placed successfully!', 'success')
            return redirect(url_for('order_confirmation', order_id=order.id))
        else:
            flash('Failed to submit order. Please try again.', 'error')

    return render_template('checkout.html',
                           cart_items=cart_items,
                           amazon_data=amazon_data,
                           user=current_user)


@app.route('/order/<int:order_id>/confirmation')
@login_required
def order_confirmation(order_id):
    """
    Order confirmation page

    Process Flow Step: Widget sends users confirmation email
    """
    order = Order.query.get_or_404(order_id)

    if order.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))

    checkout_service = get_checkout_service()
    order_summary = checkout_service.get_order_summary(order)

    return render_template('order_confirmation.html', order=order, summary=order_summary)


@app.route('/orders')
@login_required
def orders():
    """View all orders"""
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=user_orders)


@app.route('/account')
@login_required
def account():
    """User account page with settings and payment options"""
    return render_template('account.html')


# ============================================================================
# Widget API Routes (for PCP integration)
# ============================================================================

@app.route('/api/widget/config', methods=['POST'])
def widget_config():
    """
    Get widget configuration for a recipe page

    Called by embedded widget to get configuration
    """
    data = request.get_json()
    api_key = data.get('api_key')
    recipe_url = data.get('recipe_url')

    if not api_key or not recipe_url:
        return jsonify({'error': 'Missing api_key or recipe_url'}), 400

    pcp = PartnerContentProvider.query.filter_by(api_key=api_key, is_active=True).first()
    if not pcp:
        return jsonify({'error': 'Invalid API key'}), 401

    config = WidgetService.get_widget_config(pcp, recipe_url)
    return jsonify(config)


@app.route('/api/widget/ingredients', methods=['POST'])
def widget_get_ingredients():
    """
    Get ingredients and Amazon Fresh data for a recipe URL

    Process Flow: Widget accesses local storage → Merge with Amazon Fresh data
    """
    data = request.get_json()
    api_key = data.get('api_key')
    recipe_url = data.get('recipe_url')

    if not api_key or not recipe_url:
        return jsonify({'error': 'Missing api_key or recipe_url'}), 400

    pcp = PartnerContentProvider.query.filter_by(api_key=api_key, is_active=True).first()
    if not pcp:
        return jsonify({'error': 'Invalid API key'}), 401

    # Check local storage cache
    local_storage = get_local_storage_service()
    cached = local_storage.get_cached_data(recipe_url)

    if cached and cached.get('recipe_data'):
        ingredients = cached['recipe_data'].get('ingredients', [])
    else:
        # Parse recipe using schema
        schema_service = get_schema_service()
        schema = schema_service.get_schema_for_url(pcp.id, recipe_url)

        # Use parser with schema if available
        ingredients = parser.get_ingredients(recipe_url)

        # Cache the data
        local_storage.cache_recipe_data(recipe_url, {
            'ingredients': ingredients,
            'url': recipe_url
        }, pcp_id=pcp.id)

    # Get Amazon Fresh data package
    amazon_data = amazon_fresh_service.get_amazon_fresh_data_package(ingredients)

    # Cache Amazon Fresh data
    local_storage.cache_amazon_fresh_data(recipe_url, amazon_data)

    return jsonify({
        'ingredients': ingredients,
        'amazon_fresh_data': amazon_data,
        'pcp': pcp.to_dict()
    })


# ============================================================================
# PCP Management Routes
# ============================================================================

@app.route('/pcp/register', methods=['GET', 'POST'])
def pcp_register():
    """Register as a Partner Content Provider"""
    if request.method == 'POST':
        name = request.form.get('name')
        domain = request.form.get('domain')

        if not name or not domain:
            flash('Name and domain are required', 'error')
            return render_template('pcp_register.html')

        # Check if domain already registered
        if PartnerContentProvider.query.filter_by(domain=domain).first():
            flash('This domain is already registered', 'error')
            return render_template('pcp_register.html')

        # Create PCP
        api_key = WidgetService.generate_api_key()
        pcp = PartnerContentProvider(
            name=name,
            domain=domain,
            api_key=api_key
        )
        db.session.add(pcp)

        # Create default schema
        schema_service = get_schema_service()
        db.session.flush()
        schema_service.create_default_schema(pcp.id)

        db.session.commit()

        flash('Registration successful!', 'success')
        return render_template('pcp_success.html', pcp=pcp, api_key=api_key)

    return render_template('pcp_register.html')


@app.route('/pcp/embed-code/<api_key>')
def pcp_embed_code(api_key):
    """Get embed code for a PCP"""
    pcp = PartnerContentProvider.query.filter_by(api_key=api_key).first_or_404()
    embed_code = WidgetService.generate_embed_code(api_key)
    return render_template('pcp_embed.html', pcp=pcp, embed_code=embed_code)


# ============================================================================
# API Routes
# ============================================================================

@app.route('/api/toggle-ingredient/<int:ingredient_id>', methods=['POST'])
@login_required
def toggle_ingredient(ingredient_id):
    """Toggle ingredient in/out of cart"""
    ingredient = Ingredient.query.get_or_404(ingredient_id)

    if ingredient.recipe.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    ingredient.in_cart = not ingredient.in_cart
    db.session.commit()

    return jsonify({'success': True, 'in_cart': ingredient.in_cart})


@app.route('/api/delete-recipe/<int:recipe_id>', methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    """Delete a recipe"""
    recipe = Recipe.query.get_or_404(recipe_id)

    if recipe.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    db.session.delete(recipe)
    db.session.commit()

    return jsonify({'success': True})


@app.route('/api/amazon-fresh/products', methods=['POST'])
@login_required
def get_amazon_fresh_products():
    """Get Amazon Fresh products for ingredients"""
    data = request.get_json()
    ingredients = data.get('ingredients', [])

    amazon_data = amazon_fresh_service.get_amazon_fresh_data_package(ingredients)
    return jsonify(amazon_data)


# ============================================================================
# CLI Commands
# ============================================================================

@app.cli.command()
def init_db():
    """Initialize the database"""
    db.create_all()
    print('Database initialized!')


@app.cli.command()
def download_nltk_data():
    """Download required NLTK data"""
    import nltk
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('maxent_ne_chunker')
    nltk.download('words')
    print('NLTK data downloaded!')


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
