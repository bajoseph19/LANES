"""
Test script for the recipe parser
"""
from recipe_parser import RecipeParser
from bs4 import BeautifulSoup

# Create a sample recipe HTML
sample_recipe_html = """
<html>
<body>
    <h1>Chocolate Chip Cookies</h1>
    <div class="recipe-ingredients">
        <h2>Ingredients</h2>
        <ul class="ingredients">
            <li itemprop="recipeIngredient">2 cups all-purpose flour</li>
            <li itemprop="recipeIngredient">1 teaspoon baking soda</li>
            <li itemprop="recipeIngredient">1/2 teaspoon salt</li>
            <li itemprop="recipeIngredient">1 cup butter, softened</li>
            <li itemprop="recipeIngredient">3/4 cup granulated sugar</li>
            <li itemprop="recipeIngredient">3/4 cup brown sugar</li>
            <li itemprop="recipeIngredient">2 eggs</li>
            <li itemprop="recipeIngredient">2 teaspoons vanilla extract</li>
            <li itemprop="recipeIngredient">2 cups chocolate chips</li>
        </ul>
    </div>
    <div class="recipe-instructions">
        <h2>Instructions</h2>
        <ol>
            <li>Preheat oven to 375 degrees F.</li>
            <li>Mix flour, baking soda, and salt in a bowl.</li>
            <li>Beat butter and sugars until creamy.</li>
        </ol>
    </div>
</body>
</html>
"""

def test_parser():
    parser = RecipeParser()
    
    # Test semantic markup extraction
    soup = BeautifulSoup(sample_recipe_html, 'html.parser')
    ingredients = parser._extract_by_semantic_markup(soup)
    
    print("Testing Recipe Parser")
    print("=" * 50)
    print(f"\nFound {len(ingredients)} ingredients using semantic markup:")
    for i, ing in enumerate(ingredients, 1):
        print(f"  {i}. {ing}")
    
    # Test ingredient detail parsing
    if ingredients:
        print("\nTesting ingredient detail parsing:")
        sample_ing = ingredients[0]
        details = parser.parse_ingredient_details(sample_ing)
        print(f"  Raw: {sample_ing}")
        print(f"  Parsed: {details}")
    
    print("\n✅ Parser test completed successfully!")
    return len(ingredients) > 0

if __name__ == '__main__':
    success = test_parser()
    exit(0 if success else 1)
