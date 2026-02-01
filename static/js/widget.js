/**
 * Holistic Market Widget
 * Embeddable widget for Partner Content Provider recipe pages
 *
 * Process Flow Implementation:
 * 1. Widget checks local storage for cached data
 * 2. Widget obtains recipe page URL
 * 3. Widget runs web scraper from schema
 * 4. Widget sends data to content database
 * 5. Widget accesses Amazon Fresh data package
 */

(function() {
    'use strict';

    // Configuration
    const WIDGET_API_BASE = window.HOLISTIC_MARKET_API_URL || '/api/widget';
    const CHECKOUT_URL = window.HOLISTIC_MARKET_CHECKOUT_URL || '/checkout';

    // Widget class
    class HolisticMarketWidget {
        constructor(container) {
            this.container = container;
            this.apiKey = container.dataset.apiKey;
            this.theme = container.dataset.theme || 'light';
            this.recipeUrl = window.location.href;
            this.ingredients = [];
            this.amazonData = null;
            this.isLoading = false;

            this.init();
        }

        async init() {
            // Check local storage cache first (per process flow)
            const cachedData = this.checkLocalStorage();

            if (cachedData) {
                this.ingredients = cachedData.ingredients;
                this.amazonData = cachedData.amazonData;
                this.render();
            } else {
                this.renderLoading();
                await this.fetchIngredients();
            }
        }

        checkLocalStorage() {
            /**
             * Process Flow: "Recipe page 'information' is null" check
             * Check if we have cached data for this URL
             */
            try {
                const cacheKey = `hm_widget_${this.hashUrl(this.recipeUrl)}`;
                const cached = localStorage.getItem(cacheKey);

                if (cached) {
                    const data = JSON.parse(cached);
                    const cacheAge = Date.now() - data.timestamp;

                    // Cache valid for 1 hour
                    if (cacheAge < 3600000) {
                        return data;
                    }
                }
            } catch (e) {
                console.warn('HM Widget: Could not access local storage', e);
            }
            return null;
        }

        saveToLocalStorage(ingredients, amazonData) {
            /**
             * Process Flow: Cache recipe and Amazon Fresh data
             */
            try {
                const cacheKey = `hm_widget_${this.hashUrl(this.recipeUrl)}`;
                const data = {
                    ingredients: ingredients,
                    amazonData: amazonData,
                    timestamp: Date.now()
                };
                localStorage.setItem(cacheKey, JSON.stringify(data));
            } catch (e) {
                console.warn('HM Widget: Could not save to local storage', e);
            }
        }

        hashUrl(url) {
            // Simple hash function for URL
            let hash = 0;
            for (let i = 0; i < url.length; i++) {
                const char = url.charCodeAt(i);
                hash = ((hash << 5) - hash) + char;
                hash = hash & hash;
            }
            return Math.abs(hash).toString(36);
        }

        async fetchIngredients() {
            /**
             * Process Flow:
             * 1. Widget obtains recipe page URL
             * 2. Widget runs web scraper from schema
             * 3. Widget sends data to content database
             * 4. Merge with Amazon Fresh data
             */
            this.isLoading = true;

            try {
                const response = await fetch(`${WIDGET_API_BASE}/ingredients`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        api_key: this.apiKey,
                        recipe_url: this.recipeUrl
                    })
                });

                if (!response.ok) {
                    throw new Error(`API error: ${response.status}`);
                }

                const data = await response.json();
                this.ingredients = data.ingredients || [];
                this.amazonData = data.amazon_fresh_data || null;

                // Cache the data
                this.saveToLocalStorage(this.ingredients, this.amazonData);

                this.render();
            } catch (error) {
                console.error('HM Widget: Error fetching ingredients', error);
                this.renderError();
            }

            this.isLoading = false;
        }

        renderLoading() {
            this.container.innerHTML = `
                <div class="hm-widget hm-widget-${this.theme}">
                    <div class="hm-widget-header">
                        <span class="hm-logo">Holistic Market</span>
                    </div>
                    <div class="hm-widget-body hm-loading">
                        <div class="hm-spinner"></div>
                        <p>Loading ingredients...</p>
                    </div>
                </div>
            `;
            this.injectStyles();
        }

        renderError() {
            this.container.innerHTML = `
                <div class="hm-widget hm-widget-${this.theme}">
                    <div class="hm-widget-header">
                        <span class="hm-logo">Holistic Market</span>
                    </div>
                    <div class="hm-widget-body hm-error">
                        <p>Unable to load ingredients.</p>
                        <button class="hm-btn hm-btn-retry" onclick="location.reload()">Retry</button>
                    </div>
                </div>
            `;
            this.injectStyles();
        }

        render() {
            /**
             * Main widget render - shows ingredients and checkout button
             */
            const ingredientCount = this.ingredients.length;
            const total = this.amazonData ? `$${this.amazonData.total}` : '';

            this.container.innerHTML = `
                <div class="hm-widget hm-widget-${this.theme}">
                    <div class="hm-widget-header">
                        <span class="hm-logo">Holistic Market</span>
                    </div>
                    <div class="hm-widget-body">
                        <h3 class="hm-title">Buy Ingredients</h3>
                        <p class="hm-subtitle">${ingredientCount} ingredients found</p>

                        ${this.amazonData ? `
                        <div class="hm-price-summary">
                            <span class="hm-price-label">Estimated Total</span>
                            <span class="hm-price-value">${total}</span>
                        </div>
                        ` : ''}

                        <button class="hm-btn hm-btn-checkout" id="hm-checkout-btn">
                            Shop with Amazon Fresh
                        </button>

                        <p class="hm-delivery">Delivery in 2-4 hours</p>

                        <div class="hm-ingredients-preview" id="hm-ingredients-toggle">
                            <span>View Ingredients</span>
                        </div>

                        <div class="hm-ingredients-list" id="hm-ingredients-list" style="display: none;">
                            ${this.ingredients.slice(0, 10).map(ing => `
                                <div class="hm-ingredient-item">${ing}</div>
                            `).join('')}
                            ${this.ingredients.length > 10 ? `
                                <div class="hm-ingredient-more">+${this.ingredients.length - 10} more</div>
                            ` : ''}
                        </div>
                    </div>
                    <div class="hm-widget-footer">
                        <span class="hm-powered-by">Fulfilled by Amazon Fresh</span>
                    </div>
                </div>
            `;

            this.injectStyles();
            this.bindEvents();
        }

        bindEvents() {
            // Checkout button
            const checkoutBtn = document.getElementById('hm-checkout-btn');
            if (checkoutBtn) {
                checkoutBtn.addEventListener('click', () => this.handleCheckout());
            }

            // Ingredients toggle
            const toggleBtn = document.getElementById('hm-ingredients-toggle');
            const ingredientsList = document.getElementById('hm-ingredients-list');
            if (toggleBtn && ingredientsList) {
                toggleBtn.addEventListener('click', () => {
                    const isVisible = ingredientsList.style.display !== 'none';
                    ingredientsList.style.display = isVisible ? 'none' : 'block';
                    toggleBtn.querySelector('span').textContent = isVisible ? 'View Ingredients' : 'Hide Ingredients';
                });
            }
        }

        handleCheckout() {
            /**
             * Process Flow: User clicks on "Holistic Market Widget" to purchase recipe
             * Opens checkout flow with ingredients
             */
            // Store ingredients for checkout
            sessionStorage.setItem('hm_checkout_ingredients', JSON.stringify({
                ingredients: this.ingredients,
                amazonData: this.amazonData,
                sourceUrl: this.recipeUrl
            }));

            // Open checkout in new window or redirect
            window.open(`${CHECKOUT_URL}?source=widget&url=${encodeURIComponent(this.recipeUrl)}`, '_blank');
        }

        injectStyles() {
            if (document.getElementById('hm-widget-styles')) return;

            const styles = document.createElement('style');
            styles.id = 'hm-widget-styles';
            styles.textContent = `
                .hm-widget {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 320px;
                    margin: 20px auto;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    overflow: hidden;
                }

                .hm-widget-light {
                    background: #ffffff;
                    color: #333;
                }

                .hm-widget-dark {
                    background: #1a1a2e;
                    color: #eee;
                }

                .hm-widget-header {
                    background: #4a6fa5;
                    color: white;
                    padding: 12px 16px;
                    text-align: center;
                }

                .hm-logo {
                    font-weight: 600;
                    font-size: 14px;
                }

                .hm-widget-body {
                    padding: 20px;
                    text-align: center;
                }

                .hm-title {
                    margin: 0 0 8px 0;
                    font-size: 20px;
                    font-weight: 600;
                }

                .hm-subtitle {
                    margin: 0 0 16px 0;
                    color: #666;
                    font-size: 14px;
                }

                .hm-price-summary {
                    background: #f5f5f5;
                    padding: 12px;
                    border-radius: 8px;
                    margin-bottom: 16px;
                }

                .hm-price-label {
                    display: block;
                    font-size: 12px;
                    color: #666;
                }

                .hm-price-value {
                    font-size: 24px;
                    font-weight: 700;
                    color: #2e7d32;
                }

                .hm-btn {
                    display: block;
                    width: 100%;
                    padding: 14px 20px;
                    border: none;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: background 0.2s;
                }

                .hm-btn-checkout {
                    background: #ff9900;
                    color: #111;
                }

                .hm-btn-checkout:hover {
                    background: #e68a00;
                }

                .hm-btn-retry {
                    background: #4a6fa5;
                    color: white;
                }

                .hm-delivery {
                    margin: 12px 0 0 0;
                    font-size: 13px;
                    color: #2e7d32;
                }

                .hm-ingredients-preview {
                    margin-top: 16px;
                    padding: 8px;
                    cursor: pointer;
                    color: #4a6fa5;
                    font-size: 14px;
                }

                .hm-ingredients-preview:hover {
                    text-decoration: underline;
                }

                .hm-ingredients-list {
                    margin-top: 12px;
                    text-align: left;
                    max-height: 200px;
                    overflow-y: auto;
                    border-top: 1px solid #eee;
                    padding-top: 12px;
                }

                .hm-ingredient-item {
                    padding: 6px 0;
                    font-size: 13px;
                    border-bottom: 1px solid #f0f0f0;
                }

                .hm-ingredient-more {
                    padding: 8px 0;
                    font-size: 13px;
                    color: #666;
                    font-style: italic;
                }

                .hm-widget-footer {
                    padding: 12px;
                    background: #fafafa;
                    text-align: center;
                    border-top: 1px solid #eee;
                }

                .hm-powered-by {
                    font-size: 12px;
                    color: #999;
                }

                .hm-loading, .hm-error {
                    padding: 40px 20px;
                }

                .hm-spinner {
                    width: 30px;
                    height: 30px;
                    border: 3px solid #f0f0f0;
                    border-top-color: #4a6fa5;
                    border-radius: 50%;
                    animation: hm-spin 1s linear infinite;
                    margin: 0 auto 12px;
                }

                @keyframes hm-spin {
                    to { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(styles);
        }
    }

    // Initialize widgets on page load
    function initWidgets() {
        const containers = document.querySelectorAll('#holistic-market-widget, [data-holistic-market-widget]');
        containers.forEach(container => {
            if (!container.dataset.hmInitialized) {
                new HolisticMarketWidget(container);
                container.dataset.hmInitialized = 'true';
            }
        });
    }

    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initWidgets);
    } else {
        initWidgets();
    }

    // Expose to global scope for manual initialization
    window.HolisticMarketWidget = HolisticMarketWidget;
    window.initHolisticMarketWidgets = initWidgets;
})();
