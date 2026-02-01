"""
Widget Service Module
Handles Holistic Market widget embedding and PCP integration
"""
import secrets
import hashlib
import re
from urllib.parse import urlparse
from datetime import datetime, timedelta


class WidgetService:
    """Service for managing embeddable widgets for Partner Content Providers"""

    @staticmethod
    def generate_api_key():
        """Generate a unique API key for a PCP"""
        return secrets.token_hex(32)

    @staticmethod
    def generate_widget_id(pcp_domain, recipe_url):
        """Generate a unique widget ID for a recipe page"""
        combined = f"{pcp_domain}:{recipe_url}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    @staticmethod
    def extract_domain(url):
        """Extract domain from URL"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain

    @staticmethod
    def normalize_url(url):
        """Normalize URL for consistent caching"""
        parsed = urlparse(url)
        # Remove query params and fragments, lowercase
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".lower()
        # Remove trailing slash
        return normalized.rstrip('/')

    @staticmethod
    def url_hash(url):
        """Generate hash for URL (used for local storage cache)"""
        normalized = WidgetService.normalize_url(url)
        return hashlib.sha256(normalized.encode()).hexdigest()

    @staticmethod
    def match_url_pattern(url, pattern):
        """Check if URL matches a PCP schema pattern"""
        if not pattern:
            return True
        try:
            return bool(re.match(pattern, url))
        except re.error:
            return False

    @staticmethod
    def generate_embed_code(pcp_api_key, widget_host="https://widget.holisticmarket.com"):
        """
        Generate the embed code for PCPs to add to their recipe pages

        This is what PCPs add to their HTML to embed the Holistic Market widget
        """
        embed_code = f'''<!-- Holistic Market Widget -->
<div id="holistic-market-widget" data-api-key="{pcp_api_key}"></div>
<script src="{widget_host}/widget.js" async></script>
<style>
  #holistic-market-widget {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    max-width: 400px;
    margin: 20px auto;
  }}
</style>
<!-- End Holistic Market Widget -->'''
        return embed_code

    @staticmethod
    def get_widget_config(pcp, recipe_url):
        """Get widget configuration for a specific recipe page"""
        return {
            'pcp_id': pcp.id,
            'pcp_name': pcp.name,
            'recipe_url': recipe_url,
            'widget_id': WidgetService.generate_widget_id(pcp.domain, recipe_url),
            'features': {
                'show_ingredients': True,
                'show_prices': True,
                'enable_checkout': True,
                'fulfillment_partners': ['amazon_fresh']
            }
        }


class LocalStorageService:
    """Service for managing local storage cache"""

    def __init__(self, db, LocalStorageCache):
        self.db = db
        self.LocalStorageCache = LocalStorageCache

    def get_cached_data(self, url):
        """
        Check local storage for cached recipe data

        Returns cached data if available and not expired, None otherwise
        """
        url_hash = WidgetService.url_hash(url)
        cache = self.LocalStorageCache.query.filter_by(url_hash=url_hash).first()

        if cache and not cache.is_expired():
            return {
                'recipe_data': cache.get_recipe_data(),
                'amazon_fresh_data': cache.get_amazon_fresh_data(),
                'cached_at': cache.updated_at
            }
        return None

    def cache_recipe_data(self, url, recipe_data, pcp_id=None, ttl_hours=24):
        """
        Cache recipe data for a URL

        Implements: "Recipe page 'information' is null" check in process flow
        """
        url_hash = WidgetService.url_hash(url)
        cache = self.LocalStorageCache.query.filter_by(url_hash=url_hash).first()

        if not cache:
            cache = self.LocalStorageCache(
                url_hash=url_hash,
                url=url,
                pcp_id=pcp_id
            )
            self.db.session.add(cache)

        cache.set_recipe_data(recipe_data)
        cache.expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
        self.db.session.commit()
        return cache

    def cache_amazon_fresh_data(self, url, amazon_fresh_data, ttl_hours=1):
        """
        Cache Amazon Fresh product data for a URL

        Implements: "Amazon Fresh product data is null" check in process flow
        """
        url_hash = WidgetService.url_hash(url)
        cache = self.LocalStorageCache.query.filter_by(url_hash=url_hash).first()

        if cache:
            cache.set_amazon_fresh_data(amazon_fresh_data)
            cache.updated_at = datetime.utcnow()
            self.db.session.commit()
        return cache

    def invalidate_cache(self, url):
        """Invalidate cached data for a URL"""
        url_hash = WidgetService.url_hash(url)
        cache = self.LocalStorageCache.query.filter_by(url_hash=url_hash).first()
        if cache:
            self.db.session.delete(cache)
            self.db.session.commit()


class SchemaService:
    """Service for managing PCP web scraping schemas"""

    def __init__(self, db, PCPSchema):
        self.db = db
        self.PCPSchema = PCPSchema

    def get_schema_for_url(self, pcp_id, url):
        """
        Get the appropriate schema for scraping a URL

        Implements: "Obtain PCP schema information" in process flow
        """
        schemas = self.PCPSchema.query.filter_by(
            pcp_id=pcp_id,
            is_active=True
        ).all()

        for schema in schemas:
            if WidgetService.match_url_pattern(url, schema.url_pattern):
                return schema

        # Return first active schema if no pattern match
        return schemas[0] if schemas else None

    def create_default_schema(self, pcp_id):
        """Create a default schema for a new PCP"""
        schema = self.PCPSchema(
            pcp_id=pcp_id,
            name='Default Schema',
            selector_type='css',
            ingredient_selector='[itemprop="recipeIngredient"], .ingredient, .ingredients li',
            title_selector='h1, [itemprop="name"]',
            url_pattern=None  # Match all URLs
        )
        self.db.session.add(schema)
        self.db.session.commit()
        return schema
