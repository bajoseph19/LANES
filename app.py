"""
LANES - Recipe Parser Web Application
Main Flask application for converting recipe URLs into ingredient shopping carts
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from recipe_parser import RecipeParser

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lanes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize the recipe parser
parser = RecipeParser()


# Database Models
class User(UserMixin, db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    recipes = db.relationship('Recipe', backref='user', lazy=True)
    
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


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Routes
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
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('signup.html')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('signup.html')
        
        # Create new user
        user = User(email=email)
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
            # Parse the recipe
            ingredients = parser.get_ingredients(url)
            
            if not ingredients:
                flash('Could not extract ingredients from this URL. Please try another recipe.', 'warning')
                return render_template('parse_recipe.html')
            
            # Try to extract recipe title from URL
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.replace('www.', '')
            path_parts = [p for p in parsed_url.path.split('/') if p]
            
            # Use the last meaningful path segment as title, or domain if not available
            if path_parts:
                title = path_parts[-1].replace('-', ' ').replace('_', ' ').title()
            else:
                title = f"Recipe from {domain}"
            
            # Limit title length
            if len(title) > 100:
                title = title[:97] + '...'
            
            # Save recipe to database
            recipe = Recipe(user_id=current_user.id, url=url, title=title)
            db.session.add(recipe)
            db.session.flush()  # Get recipe.id
            
            # Save ingredients
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
    
    # Ensure user owns this recipe
    if recipe.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('recipe.html', recipe=recipe)


@app.route('/cart')
@login_required
def cart():
    """View shopping cart with all ingredients from saved recipes"""
    # Get all recipes for current user
    recipes = Recipe.query.filter_by(user_id=current_user.id).all()
    
    # Collect all ingredients marked as in_cart
    cart_items = []
    for recipe in recipes:
        for ingredient in recipe.ingredients:
            if ingredient.in_cart:
                cart_items.append({
                    'id': ingredient.id,
                    'text': ingredient.text,
                    'recipe_url': recipe.url,
                    'recipe_id': recipe.id
                })
    
    return render_template('cart.html', cart_items=cart_items)


@app.route('/api/toggle-ingredient/<int:ingredient_id>', methods=['POST'])
@login_required
def toggle_ingredient(ingredient_id):
    """Toggle ingredient in/out of cart"""
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    
    # Verify ownership
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
    
    # Verify ownership
    if recipe.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    db.session.delete(recipe)
    db.session.commit()
    
    return jsonify({'success': True})


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


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
