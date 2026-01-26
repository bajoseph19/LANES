# LANES API Documentation

## Overview

LANES provides both web UI and API endpoints for recipe parsing and management.

## Authentication

LANES uses session-based authentication with Flask-Login. Users must be logged in to access most endpoints.

### Sign Up
**POST** `/signup`

Create a new user account.

**Form Parameters:**
- `email` (string, required): User email address
- `password` (string, required): Password (minimum 6 characters)

**Response:**
- Success: Redirect to `/dashboard`
- Error: Display flash message and stay on signup page

**Example:**
```bash
curl -X POST http://localhost:5000/signup \
  -F "email=user@example.com" \
  -F "password=secure123"
```

### Login
**POST** `/login`

Authenticate existing user.

**Form Parameters:**
- `email` (string, required): User email address
- `password` (string, required): User password

**Response:**
- Success: Redirect to `/dashboard`
- Error: Display flash message

### Logout
**GET** `/logout`

Log out current user.

**Response:**
- Redirect to `/` (homepage)

---

## Recipe Management

### Parse Recipe
**POST** `/parse-recipe`

Parse a recipe from a URL and extract ingredients.

**Authentication:** Required

**Form Parameters:**
- `url` (string, required): Recipe URL (must be http:// or https://)

**Response:**
- Success: Redirect to `/recipe/<recipe_id>`
- Error: Flash message with error details

**Example:**
```bash
curl -X POST http://localhost:5000/parse-recipe \
  -F "url=https://www.allrecipes.com/recipe/12345/sample/" \
  --cookie "session=..."
```

**Security:**
- URL must use http or https scheme
- Localhost and private IP addresses are blocked
- 10-second timeout on requests

### View Recipe
**GET** `/recipe/<recipe_id>`

View a specific recipe and its ingredients.

**Authentication:** Required

**URL Parameters:**
- `recipe_id` (integer): Recipe ID

**Response:**
- HTML page with recipe details and ingredients
- 404 if recipe not found
- 403 if user doesn't own the recipe

### Dashboard
**GET** `/dashboard`

View all saved recipes for current user.

**Authentication:** Required

**Response:**
- HTML page with list of user's recipes

### Delete Recipe
**POST** `/api/delete-recipe/<recipe_id>`

Delete a recipe and all its ingredients.

**Authentication:** Required

**URL Parameters:**
- `recipe_id` (integer): Recipe ID to delete

**Response:**
```json
{
  "success": true
}
```

**Error Response:**
```json
{
  "error": "Access denied"
}
```

---

## Shopping Cart

### View Cart
**GET** `/cart`

View shopping cart with all ingredients from saved recipes.

**Authentication:** Required

**Response:**
- HTML page with cart items

**Cart Item Structure:**
```javascript
{
  "id": 123,
  "text": "2 cups flour",
  "recipe_url": "https://...",
  "recipe_id": 5
}
```

### Toggle Ingredient
**POST** `/api/toggle-ingredient/<ingredient_id>`

Toggle an ingredient in/out of the shopping cart.

**Authentication:** Required

**URL Parameters:**
- `ingredient_id` (integer): Ingredient ID

**Response:**
```json
{
  "success": true,
  "in_cart": true
}
```

**Error Response:**
```json
{
  "error": "Access denied"
}
```

---

## Data Models

### User
```python
{
  "id": integer,
  "email": string,
  "created_at": datetime
}
```

### Recipe
```python
{
  "id": integer,
  "user_id": integer,
  "url": string,
  "title": string,
  "created_at": datetime
}
```

### Ingredient
```python
{
  "id": integer,
  "recipe_id": integer,
  "text": string,
  "quantity": string (optional),
  "unit": string (optional),
  "item": string (optional),
  "in_cart": boolean
}
```

---

## Parser Capabilities

The recipe parser uses multiple strategies to extract ingredients:

### 1. Semantic Markup Detection
Looks for standard recipe markup:
- Schema.org `itemprop="recipeIngredient"`
- Common CSS classes: `.ingredient`, `.recipe-ingredients li`
- Common IDs: `#ingredients li`

### 2. Food Word Density Analysis
Identifies sections with high concentration of food-related terms:
- Minimum 25% food word density
- Uses vocabulary of 1000+ ingredient terms
- Recognizes collocation phrases

### 3. List-Based Extraction
Finds list elements (`<ul>`, `<ol>`) containing food words:
- Requires at least 3 items to qualify as ingredient list
- Validates each item contains food-related terms

### Supported Websites
Works best with:
- AllRecipes
- Food Network
- Tasty
- Pinterest recipe pins
- Most well-formatted food blogs

---

## Error Codes

### HTTP Status Codes
- `200 OK`: Request successful
- `302 Found`: Redirect (e.g., after login)
- `403 Forbidden`: User doesn't have access
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

### Flash Message Categories
- `success`: Operation completed successfully
- `error`: Operation failed
- `warning`: Operation completed with warnings

---

## Rate Limiting

Currently not implemented. For production, consider adding rate limiting:
- Signup: 5 requests per hour per IP
- Login: 10 requests per hour per IP
- Parse Recipe: 30 requests per hour per user

---

## Examples

### Complete User Flow

1. **Sign up**
```bash
curl -X POST http://localhost:5000/signup \
  -F "email=chef@example.com" \
  -F "password=mypassword" \
  -c cookies.txt
```

2. **Parse a recipe**
```bash
curl -X POST http://localhost:5000/parse-recipe \
  -F "url=https://www.allrecipes.com/recipe/12345/" \
  -b cookies.txt
```

3. **View cart**
```bash
curl http://localhost:5000/cart -b cookies.txt
```

4. **Toggle ingredient**
```bash
curl -X POST http://localhost:5000/api/toggle-ingredient/1 \
  -b cookies.txt
```

---

## Future API Enhancements

Planned features for future versions:
- RESTful JSON API endpoints
- API key authentication for third-party integrations
- Batch recipe import
- Recipe sharing endpoints
- Meal planning API
- Nutrition information endpoints
- Grocery delivery service integration
