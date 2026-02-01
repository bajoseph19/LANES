"""
Checkout Service Module
Handles the complete checkout flow as defined in process flows

Implements:
1. User clicks on HM Widget to purchase recipe ingredients
2. Widget prompts user for checkout information
3. User provides: Email, Name, Address, Phone number, Payment Method
4. Widget submits order to Amazon Fresh
5. Widget sends users confirmation email
"""
import secrets
import string
from datetime import datetime
from flask import url_for


class CheckoutService:
    """
    Service for managing the checkout process

    Flow:
    User → Widget → Checkout Info → Merge with Amazon Fresh Data → Order → Fulfillment
    """

    def __init__(self, db, Order, OrderItem, amazon_fresh_service):
        self.db = db
        self.Order = Order
        self.OrderItem = OrderItem
        self.amazon_fresh_service = amazon_fresh_service

    def generate_order_number(self):
        """Generate a unique order number"""
        timestamp = datetime.utcnow().strftime('%Y%m%d')
        random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        return f"HM-{timestamp}-{random_part}"

    def create_order(self, user, checkout_data, cart_items):
        """
        Create a new order from checkout data and cart items

        Implements: "User Information" → "Widget submits order to Amazon Fresh"

        Args:
            user: Current user object
            checkout_data: Dict with shipping_name, shipping_email, shipping_address,
                          shipping_phone, payment_method
            cart_items: List of ingredients/items to order
        """
        # Get Amazon Fresh data package for pricing
        ingredient_texts = [item.text if hasattr(item, 'text') else item['text'] for item in cart_items]
        amazon_data = self.amazon_fresh_service.get_amazon_fresh_data_package(ingredient_texts)

        # Create order
        order = self.Order(
            user_id=user.id,
            order_number=self.generate_order_number(),
            status='pending',
            shipping_name=checkout_data.get('shipping_name') or user.name,
            shipping_email=checkout_data.get('shipping_email') or user.email,
            shipping_address=checkout_data.get('shipping_address') or user.address,
            shipping_phone=checkout_data.get('shipping_phone') or user.phone,
            payment_method=checkout_data.get('payment_method', 'credit_card'),
            subtotal=amazon_data['subtotal'],
            tax=amazon_data['tax'],
            shipping_cost=amazon_data['delivery_fee'],
            total=amazon_data['total'],
            fulfillment_partner='amazon_fresh'
        )
        self.db.session.add(order)
        self.db.session.flush()  # Get order.id

        # Create order items
        for i, product_data in enumerate(amazon_data['products']):
            item = cart_items[i] if i < len(cart_items) else None
            order_item = self.OrderItem(
                order_id=order.id,
                ingredient_id=item.id if hasattr(item, 'id') else None,
                ingredient_text=product_data['ingredient_text'],
                product_name=product_data['product']['name'],
                quantity=product_data['quantity'],
                price=product_data['subtotal']
            )
            self.db.session.add(order_item)

        self.db.session.commit()
        return order, amazon_data

    def submit_order(self, order):
        """
        Submit order to fulfillment partner (Amazon Fresh)

        Implements: "Order" → "Order received" → "Process Order and Ship to Customer"
        """
        # Prepare order data for Amazon Fresh
        order_data = {
            'order_number': order.order_number,
            'items': [item.to_dict() for item in order.items],
            'shipping': {
                'name': order.shipping_name,
                'email': order.shipping_email,
                'address': order.shipping_address,
                'phone': order.shipping_phone
            },
            'total': order.total
        }

        # Submit to Amazon Fresh
        result = self.amazon_fresh_service.submit_order(order_data)

        if result['success']:
            order.status = 'submitted'
            order.external_order_id = result['external_order_id']
            order.submitted_at = datetime.utcnow()
            self.db.session.commit()

        return result

    def get_order_summary(self, order):
        """Get order summary for confirmation page"""
        return {
            'order_number': order.order_number,
            'status': order.status,
            'items': [
                {
                    'ingredient': item.ingredient_text,
                    'product': item.product_name,
                    'quantity': item.quantity,
                    'price': item.price
                }
                for item in order.items
            ],
            'shipping': {
                'name': order.shipping_name,
                'email': order.shipping_email,
                'address': order.shipping_address,
                'phone': order.shipping_phone
            },
            'subtotal': order.subtotal,
            'tax': order.tax,
            'shipping_cost': order.shipping_cost,
            'total': order.total,
            'fulfillment_partner': order.fulfillment_partner,
            'external_order_id': order.external_order_id,
            'created_at': order.created_at.isoformat() if order.created_at else None
        }


class EmailService:
    """
    Service for sending emails

    Implements: "Widget sends users confirmation email"

    Note: This is a mock implementation. In production, integrate with
    SendGrid, SES, or another email provider.
    """

    def __init__(self, app=None):
        self.app = app

    def send_order_confirmation(self, order, user_email):
        """
        Send order confirmation email

        In production, this would send an actual email
        """
        email_content = self._generate_confirmation_email(order)

        # Mock email sending - in production, integrate with email provider
        print(f"[EMAIL] Sending order confirmation to {user_email}")
        print(f"[EMAIL] Subject: Your Holistic Market Order #{order.order_number}")
        print(f"[EMAIL] Content preview: {email_content[:200]}...")

        return {
            'success': True,
            'recipient': user_email,
            'subject': f'Your Holistic Market Order #{order.order_number}',
            'message_id': f'msg-{order.order_number}'
        }

    def _generate_confirmation_email(self, order):
        """Generate email content for order confirmation"""
        items_text = '\n'.join([
            f"  - {item.product_name}: ${item.price:.2f}"
            for item in order.items
        ])

        return f"""
Thank you for your order!

Order Number: {order.order_number}
Status: {order.status.title()}

Shipping To:
{order.shipping_name}
{order.shipping_address}

Items:
{items_text}

Subtotal: ${order.subtotal:.2f}
Tax: ${order.tax:.2f}
Delivery: ${order.shipping_cost:.2f}
Total: ${order.total:.2f}

Your order is being processed by Amazon Fresh and will be delivered soon!

Thank you for shopping with Holistic Market.
"""

    def send_shipping_notification(self, order, tracking_info):
        """Send shipping notification email"""
        print(f"[EMAIL] Sending shipping notification for order #{order.order_number}")
        return {
            'success': True,
            'recipient': order.shipping_email,
            'subject': f'Your Order #{order.order_number} is on its way!'
        }
