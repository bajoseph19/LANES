# LANES - Recipe to Cart Parser

LANES is a web application that allows users to convert their favorite recipes from Pinterest, AllRecipes, or any food blog into an ingredient shopping cart. The application uses advanced natural language processing (NLP) to intelligently extract ingredients from recipe websites.

## Features

- 🔐 **User Authentication**: Sign up and login to save your recipes
- 🔗 **Recipe Parsing**: Simply paste a recipe URL and get ingredients extracted automatically
- 🛒 **Shopping Cart**: Manage all your ingredients in one convenient shopping list
- 🤖 **AI-Powered Parser**: Uses NLP techniques to identify ingredients with high accuracy
- 📱 **Responsive Design**: Works on desktop and mobile devices

## How It Works

The parser uses several sophisticated techniques to extract ingredients:

1. **Semantic HTML Analysis**: Looks for standard recipe markup (Schema.org, common class names)
2. **Food Word Density**: Identifies sections with high concentration of food-related terms
3. **POS Tagging**: Uses part-of-speech tagging to understand ingredient patterns (nouns, verbs, adjectives, quantifiers)
4. **Collocation Recognition**: Recognizes common ingredient phrases ("olive oil", "brown sugar", etc.)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/bajoseph19/LANES.git
cd LANES
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Download NLTK data:
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"
```

4. Initialize the database:
```bash
python app.py
# Or using Flask CLI:
flask --app app init-db
```

5. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage

1. **Sign Up**: Create an account with your email
2. **Add Recipe**: Paste a recipe URL from your favorite food website
3. **Review Ingredients**: Check the extracted ingredients list
4. **Build Cart**: Ingredients are automatically added to your shopping cart
5. **Export**: Copy your shopping list to use with grocery delivery apps

## Supported Recipe Sources

The parser works best with:
- AllRecipes
- Food Network
- Tasty
- Pinterest recipe pins
- Most food blogs with structured recipe content

## Technology Stack

- **Backend**: Flask (Python 3)
- **Database**: SQLite with Flask-SQLAlchemy
- **Authentication**: Flask-Login with password hashing
- **NLP**: NLTK (Natural Language Toolkit)
- **Web Scraping**: BeautifulSoup4, Requests
- **Frontend**: HTML5, CSS3, JavaScript

## Parser Versions

This repository contains multiple parser versions (v.1.x through v.3.0) showing the evolution of the parsing algorithm. The web application uses a modernized version based on Parser v.2.9, adapted for:
- Python 3 compatibility
- Modular architecture
- Enhanced error handling
- Multiple parsing strategies

## Future Enhancements

- Integration with grocery delivery APIs (Instacart, Amazon Fresh, etc.)
- Credit card payment processing for direct grocery ordering
- Recipe image extraction and display
- Nutrition information parsing
- Meal planning features
- Recipe sharing and collections

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.
 
