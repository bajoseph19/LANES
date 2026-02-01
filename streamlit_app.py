"""
LANES - Holistic Market Recipe Shopping App
Streamlit Application for converting recipe URLs into ingredient shopping carts
"""

# ============================================================================
# Install Dependencies at Runtime (for Streamlit Cloud)
# ============================================================================
import subprocess
import sys

def install_packages():
    """Install required packages at runtime"""
    packages = [
        'beautifulsoup4',
        'requests',
        'lxml',
        'nltk'
    ]
    for package in packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '-q'])
        except:
            pass

# Install packages before importing
install_packages()

# ============================================================================
# Now import the packages
# ============================================================================
import streamlit as st
import hashlib
import json
import os
from datetime import datetime, timedelta
import calendar

# Try to import and setup NLTK
try:
    import nltk
    nltk.download('punkt', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
except:
    pass

# Try to import recipe parser, fall back to built-in if it fails
try:
    from recipe_parser import RecipeParser
    parser = RecipeParser()
    PARSER_AVAILABLE = True
except Exception as e:
    PARSER_AVAILABLE = False
    parser = None

# ============================================================================
# Built-in Fallback Parser (when recipe_parser.py fails)
# ============================================================================

def builtin_get_ingredients(url):
    """
    Comprehensive ingredient extractor using modern schema.org standards.

    Extraction priority:
    1. JSON-LD structured data (schema.org/Recipe) - most reliable
    2. Microdata (itemprop="recipeIngredient")
    3. Common recipe plugin selectors (WPRM, Tasty, etc.)
    4. Generic CSS selectors
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        import json
        import re
        from urllib.parse import urlparse

        # Parse URL to get domain for referer
        parsed_url = urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"

        # Comprehensive headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'Referer': domain,
        }

        # Use session for better cookie handling
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=20, allow_redirects=True)

        # If still blocked, try without some headers
        if response.status_code == 403:
            simple_headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            }
            response = session.get(url, headers=simple_headers, timeout=20)

        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        ingredients = []

        # ================================================================
        # Strategy 1: JSON-LD Structured Data (schema.org Recipe)
        # This is the modern standard used by most recipe sites
        # ================================================================
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)

                # Handle both single object and array of objects
                if isinstance(data, list):
                    items = data
                else:
                    items = [data]

                for item in items:
                    # Check if it's a Recipe directly
                    if item.get('@type') == 'Recipe' or 'Recipe' in str(item.get('@type', '')):
                        recipe_ingredients = item.get('recipeIngredient', [])
                        if recipe_ingredients:
                            ingredients = recipe_ingredients if isinstance(recipe_ingredients, list) else [recipe_ingredients]
                            break

                    # Check @graph structure (common in WordPress)
                    if '@graph' in item:
                        for graph_item in item['@graph']:
                            if graph_item.get('@type') == 'Recipe' or 'Recipe' in str(graph_item.get('@type', '')):
                                recipe_ingredients = graph_item.get('recipeIngredient', [])
                                if recipe_ingredients:
                                    ingredients = recipe_ingredients if isinstance(recipe_ingredients, list) else [recipe_ingredients]
                                    break

                if ingredients:
                    break
            except (json.JSONDecodeError, TypeError, AttributeError):
                continue

        if ingredients:
            # Clean up JSON-LD ingredients
            cleaned = []
            for ing in ingredients:
                if isinstance(ing, str):
                    text = ing.strip()
                    if text and len(text) > 1:
                        cleaned.append(text)
            if cleaned:
                return cleaned[:50]

        # ================================================================
        # Strategy 2: Microdata attributes (itemprop)
        # ================================================================
        microdata_selectors = [
            '[itemprop="recipeIngredient"]',
            '[itemprop="ingredients"]',
        ]

        for selector in microdata_selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text(strip=True)
                # Clean up the text
                text = re.sub(r'\s+', ' ', text)
                if text and 2 < len(text) < 300:
                    ingredients.append(text)
            if ingredients:
                return ingredients[:50]

        # ================================================================
        # Strategy 3: Popular Recipe Plugin Selectors
        # ================================================================
        plugin_selectors = [
            # WPRM (WP Recipe Maker) - very popular
            '.wprm-recipe-ingredient',
            '.wprm-recipe-ingredients li',
            '.wprm-recipe-ingredient-group li',

            # Tasty Recipes
            '.tasty-recipes-ingredients li',
            '.tasty-recipes-ingredients-body li',
            '.tasty-recipe-ingredients li',

            # Recipe Card Blocks
            '.recipe-card-ingredients li',
            '.recipe-card__ingredient',

            # Mediavine Create
            '.mv-create-ingredients li',
            '.mv-create-ingredient',

            # Zip Recipes
            '.zlrecipe-ingredient',
            '.zip-recipe-ingredients li',

            # EasyRecipe
            '.ERSIngredients li',
            '.ingredient',

            # Yoast/Schema
            '.schema-recipe-ingredients li',

            # Jetpack Recipe
            '.jetpack-recipe-ingredients li',

            # Generic recipe classes
            '.recipe-ingredients li',
            '.ingredients-list li',
            '.ingredient-list li',
            '.recipe__ingredients li',
            '.recipe-content__ingredients li',

            # List-based ingredients
            '.ingredients li',
            '.ingredient-item',
            '.ingredientsList li',

            # Structured content
            '[data-ingredient]',
            '[class*="ingredient"] li',
        ]

        for selector in plugin_selectors:
            try:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text(strip=True)
                    text = re.sub(r'\s+', ' ', text)
                    if text and 2 < len(text) < 300 and not text.lower().startswith(('instructions', 'directions', 'steps')):
                        ingredients.append(text)
                if len(ingredients) >= 3:  # Found enough ingredients
                    return ingredients[:50]
            except:
                continue

        # ================================================================
        # Strategy 4: Find ingredients section by header
        # ================================================================
        ingredient_headers = soup.find_all(['h2', 'h3', 'h4', 'strong', 'b'],
            string=re.compile(r'ingredient', re.I))

        for header in ingredient_headers:
            # Look for the next ul/ol list
            next_list = header.find_next(['ul', 'ol'])
            if next_list:
                for li in next_list.find_all('li'):
                    text = li.get_text(strip=True)
                    text = re.sub(r'\s+', ' ', text)
                    if text and 2 < len(text) < 300:
                        ingredients.append(text)
                if ingredients:
                    return ingredients[:50]

        # ================================================================
        # Strategy 5: Last resort - find any list in recipe container
        # ================================================================
        recipe_containers = soup.select('.recipe, .recipe-container, .recipe-content, [class*="recipe"]')
        for container in recipe_containers[:3]:  # Limit search
            lists = container.find_all(['ul', 'ol'])
            for lst in lists[:2]:  # First couple lists are usually ingredients
                for li in lst.find_all('li'):
                    text = li.get_text(strip=True)
                    text = re.sub(r'\s+', ' ', text)
                    if text and 2 < len(text) < 300:
                        ingredients.append(text)
                if len(ingredients) >= 3:
                    return ingredients[:50]

        # ================================================================
        # Strategy 6: Find any list on page with food-like items
        # ================================================================
        food_indicators = ['cup', 'tbsp', 'tsp', 'tablespoon', 'teaspoon', 'oz', 'ounce',
                          'pound', 'lb', 'gram', 'kg', 'ml', 'liter', 'pinch', 'dash',
                          'chopped', 'diced', 'minced', 'sliced', 'fresh', 'dried',
                          'salt', 'pepper', 'sugar', 'flour', 'butter', 'oil', 'egg',
                          'milk', 'cream', 'cheese', 'chicken', 'beef', 'pork', 'fish',
                          'onion', 'garlic', 'tomato', 'potato', 'carrot', 'celery']

        all_lists = soup.find_all(['ul', 'ol'])
        for lst in all_lists:
            list_items = []
            for li in lst.find_all('li', recursive=False):
                text = li.get_text(strip=True)
                text = re.sub(r'\s+', ' ', text)
                if text and 3 < len(text) < 200:
                    # Check if it looks like an ingredient
                    text_lower = text.lower()
                    if any(indicator in text_lower for indicator in food_indicators):
                        list_items.append(text)
                    # Also check for number at start (like "2 cups flour")
                    elif re.match(r'^[\d½¼¾⅓⅔⅛]+', text):
                        list_items.append(text)

            if len(list_items) >= 3:
                ingredients = list_items
                return ingredients[:50]

        # ================================================================
        # Strategy 7: Look for paragraph text with ingredient patterns
        # ================================================================
        # Find the main content area
        main_content = soup.find(['article', 'main', '.post-content', '.entry-content', '.content'])
        if not main_content:
            main_content = soup.find('body')

        if main_content:
            # Look for text blocks that might list ingredients
            for elem in main_content.find_all(['p', 'div']):
                text = elem.get_text(strip=True)
                # Check if this paragraph contains a list of ingredients
                if 'ingredient' in text.lower() and len(text) < 2000:
                    # Try to split by common delimiters
                    lines = re.split(r'[,\n•·–-]', text)
                    for line in lines:
                        line = line.strip()
                        if line and 3 < len(line) < 150:
                            line_lower = line.lower()
                            if any(indicator in line_lower for indicator in food_indicators):
                                ingredients.append(line)

                    if len(ingredients) >= 3:
                        return ingredients[:50]

        return ingredients[:50]

    except Exception as e:
        return []

def get_ingredients_safe(url):
    """Get ingredients using available parser"""
    # Always try the comprehensive builtin parser first for best results
    ingredients = builtin_get_ingredients(url)
    if ingredients:
        return ingredients

    # Fallback to original parser if builtin fails
    if PARSER_AVAILABLE and parser:
        try:
            return parser.get_ingredients(url)
        except:
            pass

    return []

# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="Holistic Market",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# Custom CSS - Dark Charcoal + Green Theme
# ============================================================================

st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Root variables */
    :root {
        --bg-dark: #4a4a5c;
        --bg-darker: #3d3d4d;
        --bg-card: #5a5a6c;
        --accent: #8bc34a;
        --accent-light: #a4d465;
        --text-white: #ffffff;
        --text-muted: #b0b0b0;
    }

    /* Main app styling */
    .stApp {
        background-color: #4a4a5c;
        font-family: 'Inter', sans-serif;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Custom header */
    .app-header {
        background: linear-gradient(135deg, #3d3d4d 0%, #4a4a5c 100%);
        padding: 1rem 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        margin: -1rem -1rem 1rem -1rem;
    }

    .app-logo {
        font-size: 1.5rem;
        font-weight: 700;
        color: #8bc34a;
    }

    /* Cards */
    .card {
        background: #5a5a6c;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }

    .card-title {
        color: #ffffff;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    /* Auth card */
    .auth-card {
        background: #5a5a6c;
        border-radius: 16px;
        padding: 2rem;
        max-width: 400px;
        margin: 2rem auto;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }

    .auth-logo {
        width: 60px;
        height: 60px;
        background: linear-gradient(135deg, #8bc34a 0%, #689f38 100%);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        font-weight: 700;
        color: white;
        margin: 0 auto 1rem auto;
    }

    .auth-title {
        color: #ffffff;
        font-size: 1.5rem;
        font-weight: 600;
        text-align: center;
        margin-bottom: 0.5rem;
    }

    .auth-subtitle {
        color: #b0b0b0;
        text-align: center;
        margin-bottom: 1.5rem;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #8bc34a 0%, #7cb342 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        width: 100%;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #9ccc65 0%, #8bc34a 100%);
        transform: translateY(-1px);
    }

    /* Input fields */
    .stTextInput > div > div > input {
        background: #4a4a5c;
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 8px;
        color: #ffffff;
        padding: 0.75rem;
    }

    .stTextInput > div > div > input:focus {
        border-color: #8bc34a;
        box-shadow: 0 0 0 2px rgba(139, 195, 74, 0.2);
    }

    /* Section headers */
    .section-title {
        color: #ffffff;
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }

    /* Recipe cards */
    .recipe-card {
        background: #5a5a6c;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .recipe-icon {
        width: 50px;
        height: 50px;
        background: linear-gradient(135deg, #8bc34a 0%, #689f38 100%);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
    }

    .recipe-info {
        flex: 1;
    }

    .recipe-title {
        color: #ffffff;
        font-weight: 500;
    }

    .recipe-meta {
        color: #b0b0b0;
        font-size: 0.85rem;
    }

    /* Cart items */
    .cart-item {
        background: #5a5a6c;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .cart-item-icon {
        font-size: 1.5rem;
    }

    .cart-item-name {
        flex: 1;
        color: #ffffff;
    }

    .cart-item-price {
        color: #8bc34a;
        font-weight: 600;
    }

    /* Delivery options */
    .delivery-option {
        background: #4a4a5c;
        border: 2px solid transparent;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .delivery-option.selected {
        border-color: #8bc34a;
        background: rgba(139, 195, 74, 0.1);
    }

    .delivery-option-title {
        color: #ffffff;
        font-weight: 500;
    }

    .delivery-option-desc {
        color: #b0b0b0;
        font-size: 0.85rem;
    }

    /* Calendar widget */
    .calendar-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        color: #ffffff;
    }

    .calendar-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 4px;
    }

    .calendar-day {
        aspect-ratio: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        color: #ffffff;
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .calendar-day:hover {
        background: rgba(139, 195, 74, 0.2);
    }

    .calendar-day.selected {
        background: #8bc34a;
        color: #ffffff;
    }

    .calendar-day.today {
        border: 2px solid #8bc34a;
    }

    .calendar-day-header {
        color: #b0b0b0;
        font-size: 0.8rem;
        text-align: center;
        padding: 0.5rem;
    }

    /* Bottom navigation */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: #3d3d4d;
        display: flex;
        justify-content: space-around;
        padding: 0.75rem 0;
        border-top: 1px solid rgba(255,255,255,0.1);
        z-index: 1000;
    }

    .nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        color: #b0b0b0;
        text-decoration: none;
        font-size: 0.75rem;
        cursor: pointer;
        transition: color 0.2s ease;
    }

    .nav-item.active {
        color: #8bc34a;
    }

    .nav-icon {
        font-size: 1.25rem;
        margin-bottom: 0.25rem;
    }

    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 3rem 1rem;
        color: #b0b0b0;
    }

    .empty-state-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }

    /* Summary card */
    .summary-card {
        background: #5a5a6c;
        border-radius: 12px;
        padding: 1.5rem;
    }

    .summary-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.75rem;
        color: #ffffff;
    }

    .summary-row.total {
        border-top: 1px solid rgba(255,255,255,0.2);
        padding-top: 0.75rem;
        font-weight: 600;
        font-size: 1.1rem;
    }

    /* Hide default streamlit elements */
    div[data-testid="stToolbar"] {display: none;}
    div[data-testid="stDecoration"] {display: none;}
    div[data-testid="stStatusWidget"] {display: none;}

    /* Add padding at bottom for nav */
    .main .block-container {
        padding-bottom: 80px;
    }

    /* Text colors */
    h1, h2, h3, h4, h5, h6, p, span, label {
        color: #ffffff !important;
    }

    .text-muted {
        color: #b0b0b0 !important;
    }

    .text-accent {
        color: #8bc34a !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# Session State Initialization
# ============================================================================

def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'users_db' not in st.session_state:
        # Pre-populate with a demo account
        st.session_state.users_db = {
            'demo@holisticmarket.com': {
                'email': 'demo@holisticmarket.com',
                'password': hashlib.sha256('demo123'.encode()).hexdigest(),
                'name': 'Demo User',
                'created_at': datetime.now().isoformat()
            }
        }
    if 'recipes' not in st.session_state:
        st.session_state.recipes = []
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'
    if 'selected_delivery_date' not in st.session_state:
        st.session_state.selected_delivery_date = datetime.now() + timedelta(days=1)

init_session_state()

# ============================================================================
# Helper Functions
# ============================================================================

def hash_password(password):
    """Hash password for storage"""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(email, password):
    """Authenticate user"""
    if email in st.session_state.users_db:
        user = st.session_state.users_db[email]
        if user['password'] == hash_password(password):
            return user
    return None

def register_user(email, password, name):
    """Register new user"""
    if email in st.session_state.users_db:
        return False, "Email already registered"

    st.session_state.users_db[email] = {
        'email': email,
        'password': hash_password(password),
        'name': name,
        'created_at': datetime.now().isoformat()
    }
    return True, "Registration successful"

def get_mock_amazon_price(ingredient):
    """Get mock Amazon Fresh price for ingredient"""
    import random
    base_prices = {
        'chicken': 8.99, 'beef': 12.99, 'pork': 7.99,
        'salmon': 14.99, 'shrimp': 11.99, 'tofu': 3.99,
        'rice': 4.99, 'pasta': 2.49, 'bread': 3.49,
        'milk': 4.29, 'eggs': 5.99, 'cheese': 6.49,
        'butter': 4.99, 'oil': 7.99, 'flour': 3.99,
        'sugar': 2.99, 'salt': 1.49, 'pepper': 3.99,
        'onion': 1.29, 'garlic': 0.99, 'tomato': 2.99,
        'potato': 3.99, 'carrot': 1.99, 'celery': 2.49,
        'lettuce': 2.99, 'spinach': 3.99, 'broccoli': 2.99
    }

    ingredient_lower = ingredient.lower()
    for key, price in base_prices.items():
        if key in ingredient_lower:
            return round(price * random.uniform(0.9, 1.1), 2)

    return round(random.uniform(1.99, 9.99), 2)

# ============================================================================
# Page Components
# ============================================================================

def render_header():
    """Render app header"""
    st.markdown("""
    <div class="app-header">
        <div class="app-logo">Holistic Market</div>
        <div style="color: #b0b0b0;">
            {} {}
        </div>
    </div>
    """.format(
        f"Welcome, {st.session_state.user['name']}!" if st.session_state.authenticated else "",
        "🛒" if st.session_state.authenticated else ""
    ), unsafe_allow_html=True)

def render_bottom_nav():
    """Render bottom navigation"""
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if st.button("🏠 Main", key="nav_home", use_container_width=True):
            st.session_state.current_page = 'home'
            st.rerun()

    with col2:
        if st.button("📌 Add", key="nav_add", use_container_width=True):
            st.session_state.current_page = 'add_pin'
            st.rerun()

    with col3:
        if st.button("📋 Samples", key="nav_samples", use_container_width=True):
            st.session_state.current_page = 'samples'
            st.rerun()

    with col4:
        if st.button("🛒 Cart", key="nav_cart", use_container_width=True):
            st.session_state.current_page = 'cart'
            st.rerun()

    with col5:
        if st.button("👤 Account", key="nav_account", use_container_width=True):
            st.session_state.current_page = 'account'
            st.rerun()

# ============================================================================
# Auth Pages
# ============================================================================

def login_page():
    """Login page"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <div class="auth-logo">HM</div>
        <h1 style="margin-bottom: 0.5rem;">Welcome Back</h1>
        <p class="text-muted">Sign in to continue to Holistic Market</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        col1, col2 = st.columns(2)
        with col1:
            remember = st.checkbox("Remember me")

        submitted = st.form_submit_button("Sign In", use_container_width=True)

        if submitted:
            if email and password:
                user = authenticate(email, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.session_state.current_page = 'home'
                    st.rerun()
                else:
                    st.error("Invalid email or password")
            else:
                st.warning("Please enter email and password")

    # Demo account info
    st.markdown("""
    <div style="background: rgba(139, 195, 74, 0.1); border: 1px solid #8bc34a; border-radius: 8px; padding: 1rem; margin: 1rem 0; text-align: center;">
        <p style="margin: 0; font-size: 0.9rem;"><strong>Demo Account:</strong></p>
        <p style="margin: 0.25rem 0; font-size: 0.85rem;">Email: demo@holisticmarket.com</p>
        <p style="margin: 0; font-size: 0.85rem;">Password: demo123</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<p style='text-align: center;'>Don't have an account?</p>", unsafe_allow_html=True)
    if st.button("Create Account", use_container_width=True):
        st.session_state.current_page = 'signup'
        st.rerun()

def signup_page():
    """Signup page"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <div class="auth-logo">HM</div>
        <h1 style="margin-bottom: 0.5rem;">Create Account</h1>
        <p class="text-muted">Join Holistic Market today</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("signup_form"):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name")
        with col2:
            last_name = st.text_input("Last Name")

        email = st.text_input("Email", placeholder="you@example.com")
        phone = st.text_input("Phone Number", placeholder="(555) 123-4567")
        address = st.text_input("Address", placeholder="123 Main St")

        col1, col2 = st.columns(2)
        with col1:
            zip_code = st.text_input("Zip Code")
        with col2:
            state = st.selectbox("State", ["Select State", "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"])

        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        submitted = st.form_submit_button("Create Account", use_container_width=True)

        if submitted:
            if not all([first_name, last_name, email, password]):
                st.warning("Please fill in all required fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            else:
                name = f"{first_name} {last_name}"
                success, message = register_user(email, password, name)
                if success:
                    st.success(message)
                    user = authenticate(email, password)
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.session_state.current_page = 'home'
                    st.rerun()
                else:
                    st.error(message)

    st.markdown("---")
    st.markdown("<p style='text-align: center;'>Already have an account?</p>", unsafe_allow_html=True)
    if st.button("Sign In", use_container_width=True):
        st.session_state.current_page = 'login'
        st.rerun()

# ============================================================================
# Main Pages
# ============================================================================

def home_page():
    """Home page with recipes"""
    render_header()

    st.markdown("<h2 class='section-title'>Most Popular</h2>", unsafe_allow_html=True)

    # Popular recipes carousel (mock data)
    popular_recipes = [
        {"title": "Classic Pasta", "time": "30 min", "icon": "🍝"},
        {"title": "Grilled Chicken", "time": "45 min", "icon": "🍗"},
        {"title": "Fresh Salad", "time": "15 min", "icon": "🥗"},
        {"title": "Beef Tacos", "time": "25 min", "icon": "🌮"},
    ]

    cols = st.columns(4)
    for idx, recipe in enumerate(popular_recipes):
        with cols[idx]:
            st.markdown(f"""
            <div class="card" style="text-align: center; cursor: pointer;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{recipe['icon']}</div>
                <div class="card-title">{recipe['title']}</div>
                <div class="text-muted">{recipe['time']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<h2 class='section-title' style='margin-top: 2rem;'>Quick Actions</h2>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📌 Add Recipe Pin", use_container_width=True, key="quick_add"):
            st.session_state.current_page = 'add_pin'
            st.rerun()
    with col2:
        if st.button("🛒 View Cart", use_container_width=True, key="quick_cart"):
            st.session_state.current_page = 'cart'
            st.rerun()

    # Recent recipes
    st.markdown("<h2 class='section-title' style='margin-top: 2rem;'>Your Recent Recipes</h2>", unsafe_allow_html=True)

    if st.session_state.recipes:
        for recipe in st.session_state.recipes[-5:]:
            st.markdown(f"""
            <div class="recipe-card">
                <div class="recipe-icon">🥗</div>
                <div class="recipe-info">
                    <div class="recipe-title">{recipe['title']}</div>
                    <div class="recipe-meta">{len(recipe['ingredients'])} ingredients</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📌</div>
            <p>No recipes yet. Add your first recipe pin!</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
    render_bottom_nav()

def add_pin_page():
    """Add recipe pin page"""
    render_header()

    st.markdown("<h1>Add Recipe Pin</h1>", unsafe_allow_html=True)
    st.markdown("<p class='text-muted'>Paste a recipe URL or get a random sample</p>", unsafe_allow_html=True)

    # Initialize random_url in session state if not exists
    if 'random_url' not in st.session_state:
        st.session_state.random_url = ""

    # Get Random Recipe button
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🎲 Get Recipe", use_container_width=True):
            # Load a random URL from urls.csv
            try:
                import random
                urls_file = os.path.join(os.path.dirname(__file__), 'urls.csv')
                if os.path.exists(urls_file):
                    with open(urls_file, 'r', encoding='utf-8', errors='ignore') as f:
                        urls = [line.strip() for line in f if line.strip() and line.startswith('http')]
                    if urls:
                        st.session_state.random_url = random.choice(urls)
                        st.rerun()
            except:
                pass

    # URL input - use random_url if available
    with col1:
        url = st.text_input("Recipe URL", value=st.session_state.random_url, placeholder="https://example.com/recipe", label_visibility="collapsed")

    st.markdown("""
    <div class="card" style="text-align: center; border: 2px dashed rgba(139, 195, 74, 0.5); background: transparent;">
        <div style="font-size: 3rem; margin-bottom: 1rem;">📌</div>
        <p>Drag & drop a recipe link here</p>
        <p class="text-muted">or click "Get Recipe" for a random sample</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Extract Ingredients", use_container_width=True):
        if url:
            with st.spinner("Extracting ingredients..."):
                try:
                    ingredients = get_ingredients_safe(url)

                    if ingredients:
                        # Extract title from URL
                        from urllib.parse import urlparse
                        parsed_url = urlparse(url)
                        path_parts = [p for p in parsed_url.path.split('/') if p]
                        if path_parts:
                            title = path_parts[-1].replace('-', ' ').replace('_', ' ').title()
                        else:
                            title = f"Recipe from {parsed_url.netloc}"

                        # Save recipe
                        recipe = {
                            'id': len(st.session_state.recipes) + 1,
                            'title': title[:50],
                            'url': url,
                            'ingredients': ingredients,
                            'created_at': datetime.now().isoformat()
                        }
                        st.session_state.recipes.append(recipe)

                        # Add to cart
                        for ing in ingredients:
                            st.session_state.cart.append({
                                'text': ing,
                                'price': get_mock_amazon_price(ing),
                                'in_cart': True
                            })

                        st.success(f"Extracted {len(ingredients)} ingredients!")
                        st.session_state.random_url = ""  # Clear for next use
                        st.session_state.current_page = 'cart'
                        st.rerun()
                    else:
                        st.warning("Could not extract ingredients from this URL")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter a recipe URL")

    # Show recent ingredients if any
    if st.session_state.recipes:
        st.markdown("<h3 style='margin-top: 2rem;'>Recent Ingredients</h3>", unsafe_allow_html=True)

        latest_recipe = st.session_state.recipes[-1]
        for ing in latest_recipe['ingredients'][:5]:
            st.markdown(f"""
            <div class="cart-item">
                <input type="checkbox" checked style="width: 20px; height: 20px;">
                <span class="cart-item-name">{ing}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
    render_bottom_nav()

def cart_page():
    """Cart page with delivery options"""
    render_header()

    st.markdown("<h1>Current Cart</h1>", unsafe_allow_html=True)

    if st.session_state.cart:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("<h3>Items</h3>", unsafe_allow_html=True)

            total = 0
            for idx, item in enumerate(st.session_state.cart):
                if item.get('in_cart', True):
                    st.markdown(f"""
                    <div class="cart-item">
                        <span class="cart-item-icon">🥬</span>
                        <span class="cart-item-name">{item['text']}</span>
                        <span class="cart-item-price">${item['price']:.2f}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    total += item['price']

        with col2:
            st.markdown("<h3>Order Summary</h3>", unsafe_allow_html=True)

            tax = total * 0.08
            delivery = 0 if total > 35 else 4.99
            grand_total = total + tax + delivery

            st.markdown(f"""
            <div class="summary-card">
                <div class="summary-row">
                    <span>Subtotal ({len(st.session_state.cart)} items)</span>
                    <span>${total:.2f}</span>
                </div>
                <div class="summary-row">
                    <span>Estimated Tax</span>
                    <span>${tax:.2f}</span>
                </div>
                <div class="summary-row">
                    <span>Delivery</span>
                    <span>{'FREE' if delivery == 0 else f'${delivery:.2f}'}</span>
                </div>
                <div class="summary-row total">
                    <span>Total</span>
                    <span>${grand_total:.2f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Delivery options
            st.markdown("<h4 style='margin-top: 1.5rem;'>Delivery Options</h4>", unsafe_allow_html=True)

            delivery_type = st.radio(
                "Select delivery",
                ["Express (2-4 hrs)", "Scheduled"],
                label_visibility="collapsed"
            )

            # Calendar
            st.markdown("<h4 style='margin-top: 1rem;'>Select Date</h4>", unsafe_allow_html=True)

            selected_date = st.date_input(
                "Delivery date",
                value=datetime.now() + timedelta(days=1),
                min_value=datetime.now(),
                label_visibility="collapsed"
            )

            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

            if st.button("Checkout with Amazon Fresh", use_container_width=True, type="primary"):
                st.success("Order placed successfully!")
                st.session_state.cart = []
                st.balloons()

            st.markdown("<p class='text-muted' style='text-align: center; font-size: 0.85rem; margin-top: 0.5rem;'>Fulfilled by Amazon Fresh</p>", unsafe_allow_html=True)

        # Cart actions
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 Copy List"):
                items_text = "\n".join([f"- {item['text']}" for item in st.session_state.cart])
                st.code(items_text)
        with col2:
            if st.button("🗑️ Clear Cart"):
                st.session_state.cart = []
                st.rerun()

    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">🛒</div>
            <p>Your cart is empty</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Add a Recipe Pin", use_container_width=True):
            st.session_state.current_page = 'add_pin'
            st.rerun()

    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
    render_bottom_nav()

def account_page():
    """Account page"""
    render_header()

    if st.session_state.user:
        # User info
        st.markdown(f"""
        <div class="card" style="text-align: center;">
            <div style="width: 80px; height: 80px; background: linear-gradient(135deg, #8bc34a 0%, #689f38 100%); border-radius: 50%; margin: 0 auto 1rem; display: flex; align-items: center; justify-content: center; font-size: 2rem;">
                👤
            </div>
            <h2>{st.session_state.user['name']}</h2>
            <p class="text-muted">{st.session_state.user['email']}</p>
        </div>
        """, unsafe_allow_html=True)

        # Payment options
        st.markdown("<h3 style='margin-top: 2rem;'>Payment Options</h3>", unsafe_allow_html=True)

        payment_options = [
            {"name": "Holistic Market", "icon": "🌿", "status": "Setup"},
            {"name": "Google Pay", "icon": "🔵", "status": "Setup"},
            {"name": "Amazon Pay", "icon": "📦", "status": "Setup"},
        ]

        for option in payment_options:
            st.markdown(f"""
            <div class="card" style="display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <span style="font-size: 1.5rem;">{option['icon']}</span>
                    <span>{option['name']}</span>
                </div>
                <span class="text-accent">{option['status']}</span>
            </div>
            """, unsafe_allow_html=True)

        # Settings
        st.markdown("<h3 style='margin-top: 2rem;'>Settings</h3>", unsafe_allow_html=True)

        settings = ["Order History", "Payment Methods", "Delivery Addresses", "Notifications", "Help & Support"]

        for setting in settings:
            st.markdown(f"""
            <div class="card" style="display: flex; align-items: center; justify-content: space-between; cursor: pointer;">
                <span>{setting}</span>
                <span style="color: #b0b0b0;">›</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        if st.button("Sign Out", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.current_page = 'login'
            st.rerun()

    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
    render_bottom_nav()

def sample_recipes_page():
    """Sample recipes page with URLs from urls.csv"""
    render_header()

    st.markdown("<h1>Sample Recipes</h1>", unsafe_allow_html=True)
    st.markdown("<p class='text-muted'>Copy a URL and paste it in Add Pin to try the app</p>", unsafe_allow_html=True)

    # Load URLs from file
    urls = []
    try:
        urls_file = os.path.join(os.path.dirname(__file__), 'urls.csv')
        if os.path.exists(urls_file):
            with open(urls_file, 'r', encoding='utf-8', errors='ignore') as f:
                urls = [line.strip() for line in f if line.strip() and line.startswith('http')]
    except:
        pass

    if urls:
        # Search/filter
        search = st.text_input("🔍 Search recipes", placeholder="e.g., chicken, pasta, cake...")

        # Filter URLs
        if search:
            filtered_urls = [u for u in urls if search.lower() in u.lower()]
        else:
            filtered_urls = urls

        st.markdown(f"<p class='text-muted'>Showing {min(50, len(filtered_urls))} of {len(filtered_urls)} recipes</p>", unsafe_allow_html=True)

        # Display URLs (limit to 50 for performance)
        for idx, url in enumerate(filtered_urls[:50]):
            # Extract recipe name from URL
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                path_parts = [p for p in parsed.path.split('/') if p]
                if path_parts:
                    name = path_parts[-1].replace('-', ' ').replace('_', ' ').title()[:40]
                else:
                    name = parsed.netloc
            except:
                name = url[:40]

            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"""
                <div class="card" style="padding: 0.75rem;">
                    <div style="font-weight: 500; color: #ffffff; margin-bottom: 0.25rem;">{name}</div>
                    <div style="font-size: 0.75rem; color: #8bc34a; word-break: break-all;">{url[:60]}...</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("📋 Copy", key=f"copy_{idx}", use_container_width=True):
                    st.session_state.copied_url = url
                    st.toast(f"Copied! Go to Add Pin to paste.")

        # Show copied URL
        if 'copied_url' in st.session_state and st.session_state.copied_url:
            st.markdown(f"""
            <div style="background: rgba(139, 195, 74, 0.2); border: 1px solid #8bc34a; border-radius: 8px; padding: 1rem; margin-top: 1rem;">
                <p style="margin: 0; font-size: 0.9rem;"><strong>Copied URL:</strong></p>
                <p style="margin: 0.25rem 0; font-size: 0.8rem; word-break: break-all;">{st.session_state.copied_url}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("No sample recipes found. Make sure urls.csv exists in the app directory.")

    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
    render_bottom_nav()

# ============================================================================
# Main App Logic
# ============================================================================

def main():
    """Main app entry point"""
    if not st.session_state.authenticated:
        if st.session_state.current_page == 'signup':
            signup_page()
        else:
            login_page()
    else:
        if st.session_state.current_page == 'home':
            home_page()
        elif st.session_state.current_page == 'add_pin':
            add_pin_page()
        elif st.session_state.current_page == 'samples':
            sample_recipes_page()
        elif st.session_state.current_page == 'cart':
            cart_page()
        elif st.session_state.current_page == 'account':
            account_page()
        else:
            home_page()

if __name__ == "__main__":
    main()
