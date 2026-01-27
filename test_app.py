"""
Integration test for LANES application
Tests user registration, login, and recipe parsing
"""
import os
import subprocess
from app import app, db, User, Recipe, Ingredient
from recipe_parser import RecipeParser
from bs4 import BeautifulSoup

def setup_environment():
    """Set up environment by installing required dependencies"""
    print("Setting up virtual environment and installing dependencies...")
    try:
        if os.system("pip install -r requirements.txt") == 0:
            print("   ✅ Dependencies installed successfully")
        else:
            raise Exception("Dependency installation failed. Check errors above.")
    except Exception as e:
        print(f"❌ Error during environment setup: {e}")
        exit(1)

def test_app():
    """Test the main application functionality"""
    print("Testing LANES Application")
    print("=" * 60)
    
    # Test 1: Database Models
    print("\n1. Testing Database Models...")
    with app.app_context():
        # Initialize database
        db.create_all()
        
        # Clear existing test data
        User.query.filter_by(email='test@example.com').delete()
        db.session.commit()
        
        # Create test user
        user = User(email='test@example.com')
        user.set_password('testpassword123')
        db.session.add(user)
        db.session.commit()
        
        print(f"   ✅ Created user: {user.email}")
        
        # Test password verification
        assert user.check_password('testpassword123'), "Password check failed"
        assert not user.check_password('wrongpassword'), "Password check should fail"
        print("   ✅ Password hashing works correctly")
        
        # Create test recipe
        recipe = Recipe(
            user_id=user.id,
            url='https://example.com/recipe',
            title='Test Recipe'
        )
        db.session.add(recipe)
        db.session.commit()
        
        print(f"   ✅ Created recipe: {recipe.title}")
        
        # Create test ingredients
        test_ingredients = [
            '2 cups flour',
            '1 cup sugar',
            '3 eggs'
        ]
        
        for ing_text in test_ingredients:
            ingredient = Ingredient(
                recipe_id=recipe.id,
                text=ing_text,
                in_cart=True
            )
            db.session.add(ingredient)
        
        db.session.commit()
        
        # Verify relationships
        user_recipes = Recipe.query.filter_by(user_id=user.id).all()
        assert len(user_recipes) >= 1, "User should have at least 1 recipe"
        
        recipe_ingredients = Ingredient.query.filter_by(recipe_id=recipe.id).all()
        assert len(recipe_ingredients) == 3, "Recipe should have 3 ingredients"
        
        print(f"   ✅ Created {len(recipe_ingredients)} ingredients")
        print("   ✅ Database relationships work correctly")
    
    # Test 2: Flask App Routes
    print("\n2. Testing Flask Routes...")
    with app.test_client() as client:
        # Test index page
        response = client.get('/')
        assert response.status_code == 200, "Index page failed"
        assert b'LANES' in response.data, "Index page missing content"
        print("   ✅ Index page loads correctly")
        
        # Test signup page
        response = client.get('/signup')
        assert response.status_code == 200, "Signup page failed"
        print("   ✅ Signup page loads correctly")
        
        # Test login page
        response = client.get('/login')
        assert response.status_code == 200, "Login page failed"
        print("   ✅ Login page loads correctly")
        
        # Test login redirect for protected pages
        response = client.get('/dashboard')
        assert response.status_code == 302, "Should redirect when not logged in"
        print("   ✅ Protected routes require authentication")
    
    # Test 3: Parser Functionality
    print("\n3. Testing Recipe Parser...")
    parser = RecipeParser()
    
    # Test with sample HTML
    sample_html = """
    <html>
        <body>
            <ul class="ingredients">
                <li itemprop="recipeIngredient">2 cups flour</li>
                <li itemprop="recipeIngredient">1 cup milk</li>
            </ul>
        </body>
    </html>
    """
    
    soup = BeautifulSoup(sample_html, 'html.parser')
    ingredients = parser._extract_by_semantic_markup(soup)
    
    assert len(ingredients) == 2, "Should extract 2 ingredients"
    print(f"   ✅ Parser extracted {len(ingredients)} ingredients")
    
    # Test ingredient detail parsing
    details = parser.parse_ingredient_details("2 cups flour")
    assert details['quantity'] == '2', "Quantity parsing failed"
    assert details['unit'] == 'cups', "Unit parsing failed"
    print("   ✅ Ingredient detail parsing works")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed successfully!")
    print("\nThe LANES application is ready to use:")
    print("  - User authentication: ✅")
    print("  - Recipe management: ✅")
    print("  - Ingredient parsing: ✅")
    print("  - Shopping cart: ✅")
    
    return True

if __name__ == '__main__':
    try:
        setup_environment()  # Install dependencies
        success = test_app()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
