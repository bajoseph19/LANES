"""
Recipe Parser Module
Modernized version of Parser v.2.9 for Python 3
Extracts ingredients from recipe URLs using NLP techniques
"""
import re
import csv
import os
import requests
from bs4 import BeautifulSoup
import nltk
from collections import namedtuple


class RecipeParser:
    """Parser to extract ingredients from recipe websites"""
    
    # Configuration constants
    MAX_INGREDIENTS = 50  # Maximum number of ingredients to extract
    MIN_FOOD_DENSITY = 0.25  # Minimum ratio of food words to total words
    
    def __init__(self):
        """Initialize the parser with word lists and patterns"""
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.food_words = self._load_csv('food_words_.csv')
        self.coll_words = self._load_csv('coll_words_.csv')
        
        # Ensure NLTK data is available
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
    
    def _load_csv(self, filename):
        """Load words from CSV file"""
        words = []
        filepath = os.path.join(self.base_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"Warning: {filename} not found. Parser will use basic extraction only.")
            return words
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row:
                        words.extend(row)
        except Exception as e:
            print(f"Warning: Could not load {filename}: {e}")
        
        return [w.strip().lower() for w in words if w.strip()]
    
    def clean_text(self, text):
        """Clean and normalize text"""
        if isinstance(text, list):
            text = ' '.join(text)
        
        # Remove special characters but keep basic punctuation
        text = text.lower().strip()
        text = re.sub(r'[<>\[\]()@#$%^&*;:?"]+', '', text)
        return text
    
    def get_ingredients(self, url):
        """
        Extract ingredients from a recipe URL
        
        Args:
            url: Recipe URL to parse
            
        Returns:
            List of ingredient strings
        """
        try:
            # Fetch the webpage
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple strategies to find ingredients
            ingredients = []
            
            # Strategy 1: Look for common ingredient list patterns
            ingredients = self._extract_by_semantic_markup(soup)
            
            # Strategy 2: If no ingredients found, use food word density
            if not ingredients:
                ingredients = self._extract_by_food_density(soup)
            
            # Strategy 3: Look for lists with food words
            if not ingredients:
                ingredients = self._extract_from_lists(soup)
            
            return ingredients
            
        except Exception as e:
            print(f"Error parsing recipe: {e}")
            return []
    
    def _extract_by_semantic_markup(self, soup):
        """Extract ingredients using semantic HTML markup"""
        ingredients = []
        
        # Common ingredient markup patterns
        selectors = [
            # Schema.org microdata
            '[itemprop="recipeIngredient"]',
            '[itemprop="ingredients"]',
            # Common class names
            '.ingredient',
            '.ingredients li',
            '.recipe-ingredients li',
            '.ingredient-list li',
            # Common ID patterns
            '#ingredients li',
            '#ingredient-list li',
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text(strip=True)
                if text and len(text) > 2:
                    ingredients.append(self.clean_text(text))
            
            if ingredients:
                break
        
        return ingredients
    
    def _extract_by_food_density(self, soup):
        """Extract ingredients by finding areas with high food word density"""
        ingredients = []
        tolerance = 10
        
        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'header', 'footer']):
            script.decompose()
        
        # Look through body sections
        if soup.body:
            for parent in soup.body.find_all(['div', 'section', 'ul', 'ol']):
                text = parent.get_text(' ', strip=True)
                
                if not text:
                    continue
                
                words = text.split()
                if len(words) < 3:
                    continue
                
                # Count food words
                food_word_count = sum(1 for word in words if self.clean_text(word) in self.food_words)
                
                # Check density threshold
                density = food_word_count / len(words) if words else 0
                
                if density > self.MIN_FOOD_DENSITY:  # 25% of words are food-related
                    # This is likely an ingredients section
                    # Try to split into individual ingredients
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and len(line) > 2 and not line.endswith(':'):
                            # Check if line has food words
                            line_words = line.split()
                            line_food_count = sum(1 for w in line_words if self.clean_text(w) in self.food_words)
                            if line_food_count > 0:
                                ingredients.append(self.clean_text(line))
                    
                    if ingredients:
                        break
        
        return ingredients[:self.MAX_INGREDIENTS]  # Limit to reasonable number
    
    def _extract_from_lists(self, soup):
        """Extract ingredients from list elements containing food words"""
        ingredients = []
        
        # Find all list items
        for ul in soup.find_all(['ul', 'ol']):
            list_items = ul.find_all('li')
            list_ingredients = []
            
            for li in list_items:
                text = li.get_text(strip=True)
                if not text or len(text) < 3:
                    continue
                
                # Check if contains food words
                words = text.lower().split()
                has_food_word = any(self.clean_text(word) in self.food_words for word in words)
                
                if has_food_word:
                    list_ingredients.append(self.clean_text(text))
            
            # If this list has multiple ingredients, it's likely the ingredient list
            if len(list_ingredients) >= 3:
                ingredients = list_ingredients
                break
        
        return ingredients
    
    def parse_ingredient_details(self, ingredient_text):
        """
        Parse an ingredient string into structured components
        
        Args:
            ingredient_text: Raw ingredient string
            
        Returns:
            Dictionary with quantity, unit, item
        """
        # This is a simplified version - the full parser has complex regex patterns
        parts = {
            'quantity': '',
            'unit': '',
            'item': ingredient_text
        }
        
        # Common units
        units = ['cup', 'cups', 'tablespoon', 'tablespoons', 'tbsp', 'teaspoon', 'teaspoons', 'tsp',
                 'ounce', 'ounces', 'oz', 'pound', 'pounds', 'lb', 'lbs', 'gram', 'grams', 'g',
                 'kilogram', 'kilograms', 'kg', 'liter', 'liters', 'l', 'milliliter', 'milliliters', 'ml',
                 'can', 'cans', 'jar', 'jars', 'package', 'packages', 'clove', 'cloves']
        
        # Try to extract quantity and unit
        words = ingredient_text.split()
        
        # Look for numbers at the start
        if words and re.match(r'^\d+', words[0]):
            parts['quantity'] = words[0]
            
            # Check if next word is a unit
            if len(words) > 1 and words[1].lower() in units:
                parts['unit'] = words[1]
                parts['item'] = ' '.join(words[2:])
            else:
                parts['item'] = ' '.join(words[1:])
        
        return parts


if __name__ == '__main__':
    # Test the parser
    parser = RecipeParser()
    test_url = "https://www.allrecipes.com/recipe/12345/sample-recipe/"
    ingredients = parser.get_ingredients(test_url)
    print(f"Found {len(ingredients)} ingredients:")
    for ing in ingredients:
        print(f"  - {ing}")
