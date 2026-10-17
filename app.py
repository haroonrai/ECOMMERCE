try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import os
import secrets
from datetime import datetime
from functools import wraps
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from database import (get_db_connection, init_db, query_db, execute_db, 
                      check_password_hash, generate_password_hash, 
                      get_all_settings, get_setting, set_setting)
from seed_data import seed_database

app = Flask(__name__, template_folder='Templates', static_folder='Static', static_url_path='/static')

# Production Security & Session Configuration
is_production = os.environ.get('FLASK_ENV') == 'production' or bool(os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLY_APP_NAME'))
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'aethel_luxury_ecommerce_secret_key_2026_x8891'),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=is_production,
    TEMPLATES_AUTO_RELOAD=True,
    SEND_FILE_MAX_AGE_DEFAULT=0,
)

# Optional WhiteNoise integration for high-performance static asset serving in production
if is_production:
    try:
        from whitenoise import WhiteNoise
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Static')
        if os.path.exists(static_dir):
            app.wsgi_app = WhiteNoise(app.wsgi_app, root=static_dir, prefix='static/')
    except Exception:
        pass

@app.after_request
def add_header(response):
    if not is_production:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

@app.route('/Static/<path:filename>')
def serve_static_upper(filename):
    return send_from_directory(app.static_folder, filename)

# Auto initialize DB and conditionally seed if empty
with app.app_context():
    init_db()
    seed_database(force=False)

# Helpers
def get_cart():
    if 'cart' not in session:
        session['cart'] = {
            'items': [],
            'subtotal': 0.0,
            'discount_percent': 0.0,
            'coupon_code': None,
            'discount_amount': 0.0,
            'tax_amount': 0.0,
            'shipping_cost': 0.0,
            'total': 0.0
        }
    return session['cart']

def recalculate_cart(cart):
    subtotal = sum(item['price'] * item['quantity'] for item in cart['items'])
    cart['subtotal'] = round(subtotal, 2)
    
    # Calculate discount
    discount_pct = cart.get('discount_percent', 0.0)
    discount_amount = (subtotal * (discount_pct / 100.0)) if discount_pct > 0 else 0.0
    cart['discount_amount'] = round(discount_amount, 2)

    # Shipping (Complimentary on orders >= 150 or if cart is empty or coupon applied)
    if subtotal == 0:
        cart['shipping_cost'] = 0.0
    elif subtotal >= 150.0 or cart['discount_amount'] > 0:
        cart['shipping_cost'] = 0.0
    else:
        cart['shipping_cost'] = 15.0

    # 8% Tax
    taxable_amount = max(0.0, subtotal - discount_amount)
    cart['tax_amount'] = round(taxable_amount * 0.08, 2)

    # Grand Total
    cart['total'] = round(taxable_amount + cart['shipping_cost'] + cart['tax_amount'], 2)
    session.modified = True
    return cart

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id') or not session.get('is_admin'):
            flash('Administrator authentication required to access this portal.', 'error')
            return redirect(url_for('auth_page'))
        return f(*args, **kwargs)
    return decorated_function

# Context Processor for Global Variables
@app.context_processor
def inject_globals():
    cart = get_cart()
    cart_items_list = cart.get('items', []) if isinstance(cart, dict) else []
    cart_count = sum(item.get('quantity', 1) for item in cart_items_list)
    
    # Categories for navbar
    categories = query_db("SELECT * FROM categories ORDER BY id ASC")
    
    # Wishlist count
    wishlist_count = 0
    user_wishlist_ids = []
    user_id = session.get('user_id')
    if user_id:
        wishlist_items = query_db("SELECT product_id FROM wishlists WHERE user_id = ?", (user_id,))
        user_wishlist_ids = [item['product_id'] for item in wishlist_items]
        wishlist_count = len(user_wishlist_ids)
    elif 'guest_wishlist' in session:
        user_wishlist_ids = session['guest_wishlist']
    # Dynamic Store Settings (WhatsApp, Email, Phone, Address)
    store_settings = get_all_settings()
    wa_raw = store_settings.get('whatsapp_number', '+92 300 1234567')
    clean_whatsapp = ''.join(c for c in str(wa_raw) if c.isdigit())
    if not clean_whatsapp:
        clean_whatsapp = '923001234567'

    return {
        'cart': cart,
        'cart_count': cart_count,
        'categories': categories,
        'wishlist_count': wishlist_count,
        'user_wishlist_ids': user_wishlist_ids,
        'current_user_id': user_id,
        'store_settings': store_settings,
        'clean_whatsapp_number': clean_whatsapp
    }

# ==============================================================================
# PUBLIC STOREFRONT ROUTES
# ==============================================================================

@app.route('/')
def home():
    featured_products = query_db("""
        SELECT p.*, c.name as category_name, c.slug as category_slug 
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.id 
        WHERE p.is_featured = 1 
        ORDER BY p.id ASC 
        LIMIT 6
    """)
    trending_products = query_db("""
        SELECT p.*, c.name as category_name 
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.id 
        WHERE p.is_trending = 1 
        ORDER BY p.rating DESC 
        LIMIT 4
    """)
    categories = query_db("SELECT * FROM categories ORDER BY id ASC")
    return render_template('index.html', featured_products=featured_products, trending_products=trending_products, categories=categories)

@app.route('/shop')
def shop():
    category_slug = request.args.get('category')
    search_query = request.args.get('q', '').strip()
    sort_by = request.args.get('sort', 'newest')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')

    query = """
        SELECT p.*, c.name as category_name, c.slug as category_slug 
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.id 
        WHERE 1=1
    """
    params = []

    current_category = None
    if category_slug:
        current_category = query_db("SELECT * FROM categories WHERE slug = ?", (category_slug,), one=True)
        if current_category:
            query += " AND p.category_id = ?"
            params.append(current_category['id'])

    if search_query:
        query += " AND (p.name LIKE ? OR p.description LIKE ? OR p.short_description LIKE ?)"
        term = f"%{search_query}%"
        params.extend([term, term, term])

    if min_price:
        try:
            query += " AND p.price >= ?"
            params.append(float(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            query += " AND p.price <= ?"
            params.append(float(max_price))
        except ValueError:
            pass

    if sort_by == 'price_asc':
        query += " ORDER BY p.price ASC"
    elif sort_by == 'price_desc':
        query += " ORDER BY p.price DESC"
    elif sort_by == 'rating':
        query += " ORDER BY p.rating DESC"
    else:
        query += " ORDER BY p.created_at DESC"

    products = query_db(query, params)
    categories = query_db("SELECT * FROM categories ORDER BY id ASC")

    return render_template('shop.html', 
                           products=products, 
                           categories=categories, 
                           current_category=current_category, 
                           search_query=search_query, 
                           current_sort=sort_by,
                           min_price=min_price,
                           max_price=max_price)

@app.route('/product/<slug>')
def product_detail(slug):
    product = query_db("""
        SELECT p.*, c.name as category_name, c.slug as category_slug 
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.id 
        WHERE p.slug = ?
    """, (slug,), one=True)

    if not product:
        flash('Product not found in our catalog.', 'error')
        return redirect(url_for('shop'))

    gallery_images = query_db("SELECT * FROM product_images WHERE product_id = ?", (product['id'],))
    reviews = query_db("SELECT * FROM reviews WHERE product_id = ? ORDER BY created_at DESC", (product['id'],))
    
    related_products = query_db("""
        SELECT p.*, c.name as category_name, c.slug as category_slug 
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.id 
        WHERE p.category_id = ? AND p.id != ? 
        LIMIT 4
    """, (product['category_id'], product['id']))

    return render_template('product_detail.html', 
                           product=product, 
                           gallery_images=gallery_images, 
                           reviews=reviews, 
                           related_products=related_products)

@app.route('/product/<slug>/review', methods=['POST'])
def submit_review(slug):
    product = query_db("SELECT id FROM products WHERE slug = ?", (slug,), one=True)
    if not product:
        flash('Product not found.', 'error')
        return redirect(url_for('shop'))

    user_name = request.form.get('user_name', 'Verified Customer').strip()
    rating = int(request.form.get('rating', 5))
    title = request.form.get('title', '').strip()
    comment = request.form.get('comment', '').strip()
    user_id = session.get('user_id')

    execute_db("""
        INSERT INTO reviews (product_id, user_id, user_name, rating, title, comment) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (product['id'], user_id, user_name, rating, title, comment))

    # Recalculate average rating & review count
    stats = query_db("SELECT AVG(rating) as avg_rating, COUNT(*) as cnt FROM reviews WHERE product_id = ?", (product['id'],), one=True)
    if stats:
        avg_r = round(stats['avg_rating'] or 5.0, 1)
        cnt = stats['cnt'] or 1
        execute_db("UPDATE products SET rating = ?, review_count = ? WHERE id = ?", (avg_r, cnt, product['id']))

    flash('Thank you! Your verified review has been published.', 'success')
    return redirect(url_for('product_detail', slug=slug))

# ==============================================================================
# CART & CHECKOUT ROUTES
# ==============================================================================

@app.route('/cart')
def cart_page():
    cart = get_cart()
    cart = recalculate_cart(cart)
    return render_template('cart.html', cart=cart)

@app.route('/cart/apply-coupon', methods=['POST'])
def apply_coupon():
    code = request.form.get('coupon_code', '').strip().upper()
    cart = get_cart()

    coupon = query_db("SELECT * FROM coupons WHERE code = ? AND is_active = 1", (code,), one=True)
    if not coupon:
        flash(f'Invalid or expired coupon code: {code}', 'error')
        return redirect(url_for('cart_page'))

    if cart['subtotal'] < coupon['min_spend']:
        flash(f'Minimum spend of ${coupon["min_spend"]:.2f} required for coupon {code}.', 'error')
        return redirect(url_for('cart_page'))

    cart['coupon_code'] = coupon['code']
    cart['discount_percent'] = float(coupon['discount_percent'])
    recalculate_cart(cart)

    flash(f'Promotional code {code} applied successfully ({coupon["discount_percent"]}% OFF)!', 'success')
    return redirect(url_for('cart_page'))

@app.route('/cart/remove-coupon')
def remove_coupon():
    cart = get_cart()
    cart['coupon_code'] = None
    cart['discount_percent'] = 0.0
    recalculate_cart(cart)
    flash('Promotional code removed.', 'success')
    return redirect(url_for('cart_page'))

@app.route('/checkout')
def checkout_page():
    cart = get_cart()
    
    # Handle instant buy
    buy_now_id = request.args.get('buy_now')
    if buy_now_id:
        product = query_db("SELECT * FROM products WHERE id = ?", (buy_now_id,), one=True)
        if product:
            cart['items'] = [{
                'product_id': product['id'],
                'name': product['name'],
                'slug': product['slug'],
                'price': float(product['price']),
                'quantity': 1,
                'image_url': product['image_url']
            }]
            recalculate_cart(cart)

    if not cart['items']:
        flash('Your shopping bag is empty. Please add items to checkout.', 'error')
        return redirect(url_for('shop'))

    cart = recalculate_cart(cart)
    
    user = None
    if session.get('user_id'):
        user = query_db("SELECT * FROM users WHERE id = ?", (session['user_id'],), one=True)

    return render_template('checkout.html', cart=cart, user=user)

@app.route('/checkout/process', methods=['POST'])
def process_checkout():
    cart = get_cart()
    if not cart['items']:
        flash('Your shopping bag is empty.', 'error')
        return redirect(url_for('shop'))

    cart = recalculate_cart(cart)

    customer_name = request.form.get('customer_name', '').strip()
    customer_email = request.form.get('customer_email', '').strip()
    customer_phone = request.form.get('customer_phone', '').strip()
    shipping_address = request.form.get('shipping_address', '').strip()
    city = request.form.get('city', '').strip()
    postal_code = request.form.get('postal_code', '').strip()
    country = request.form.get('country', 'Pakistan').strip()
    shipping_method = request.form.get('shipping_method', 'Standard Shipping')
    payment_method = request.form.get('payment_method', 'Cash on Delivery (COD)').strip()

    if not customer_name or not customer_email or not shipping_address:
        flash('Please fill in all required shipping information.', 'error')
        return redirect(url_for('checkout_page'))

    # Payment details processing (COD & Direct Card)
    payment_account = ''
    transaction_reference = ''

    if 'Cash on Delivery' in payment_method or 'COD' in payment_method:
        payment_method = 'Cash on Delivery (COD)'
        payment_account = customer_phone
        transaction_reference = f"COD-{secrets.randbelow(899999) + 100000}"
        payment_status = 'Pending (Cash on Delivery)'
    else:
        payment_method = 'Credit / Debit Card'
        card_num = request.form.get('card_number', '4242').replace(' ', '')
        last4 = card_num[-4:] if len(card_num) >= 4 else '4242'
        payment_account = f"Card •••• {last4}"
        transaction_reference = f"3DS-{secrets.randbelow(899999) + 100000}"
        payment_status = 'Paid (Card 3DS Verified)'

    # Shipping and Total Calculation
    shipping_cost = 15.0 if ('VIP' in shipping_method or 'Same Day' in shipping_method) else (0.0 if (cart['subtotal'] >= 150.0 or cart['discount_amount'] > 0 or 'Standard' in shipping_method) else 15.0)
    taxable_amount = max(0.0, cart['subtotal'] - cart['discount_amount'])
    tax_amount = round(taxable_amount * 0.08, 2)
    grand_total = round(taxable_amount + shipping_cost + tax_amount, 2)

    order_number = f"ORD-{datetime.now().strftime('%Y')}-{secrets.randbelow(89999) + 10000}"
    tracking_prefix = 'AURA-EXP'
    if 'TCS' in shipping_method:
        tracking_prefix = 'TCS'
    elif 'Leopard' in shipping_method:
        tracking_prefix = 'LEO'
    elif 'CallCourier' in shipping_method:
        tracking_prefix = 'CC'
    tracking_number = f"{tracking_prefix}-{secrets.randbelow(899999) + 100000}"
    user_id = session.get('user_id')

    notes = request.form.get('notes', '').strip()
    prescription_file = request.files.get('prescription_file')
    prescription_filename = None

    if prescription_file and prescription_file.filename:
        safe_name = f"rx_{secrets.token_hex(6)}_{secure_filename(prescription_file.filename)}"
        upload_dir = os.path.join(app.static_folder, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        prescription_file.save(os.path.join(upload_dir, safe_name))
        prescription_filename = safe_name
        if notes:
            notes = f"[Prescription Attached: {safe_name}] " + notes
        else:
            notes = f"[Prescription Attached: {safe_name}]"

    order_id = execute_db("""
        INSERT INTO orders (
            order_number, user_id, customer_name, customer_email, customer_phone,
            shipping_address, city, postal_code, country, shipping_method,
            payment_method, payment_status, payment_account, transaction_reference,
            subtotal, discount_amount, shipping_cost, tax_amount, total_amount,
            coupon_code, order_status, tracking_number, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Processing', ?, ?)
    """, (
        order_number, user_id, customer_name, customer_email, customer_phone,
        shipping_address, city, postal_code, country, shipping_method,
        payment_method, payment_status, payment_account, transaction_reference,
        cart['subtotal'], cart['discount_amount'],
        shipping_cost, tax_amount, grand_total,
        cart['coupon_code'], tracking_number, notes
    ))

    # Insert items & decrease stock
    for item in cart['items']:
        execute_db("""
            INSERT INTO order_items (order_id, product_id, product_name, price, quantity, image_url)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (order_id, item['product_id'], item['name'], item['price'], item['quantity'], item['image_url']))

        execute_db("UPDATE products SET stock = MAX(0, stock - ?) WHERE id = ?", (item['quantity'], item['product_id']))

    # Clear cart
    session['cart'] = {
        'items': [],
        'subtotal': 0.0,
        'discount_percent': 0.0,
        'coupon_code': None,
        'discount_amount': 0.0,
        'tax_amount': 0.0,
        'shipping_cost': 0.0,
        'total': 0.0
    }
    session.modified = True

    flash('Your order has been placed successfully!', 'success')
    return redirect(url_for('order_confirmation', order_number=order_number))

@app.route('/orders/confirmation/<order_number>')
def order_confirmation(order_number):
    order = query_db("SELECT * FROM orders WHERE order_number = ?", (order_number,), one=True)
    if not order:
        flash('Order record not found.', 'error')
        return redirect(url_for('home'))

    items = query_db("SELECT * FROM order_items WHERE order_id = ?", (order['id'],))
    return render_template('order_confirmation.html', order=order, items=items)

@app.route('/orders')
def orders_list():
    search_q = request.args.get('q', '').strip()
    user_id = session.get('user_id')
    
    if search_q:
        orders = query_db("""
            SELECT * FROM orders 
            WHERE order_number LIKE ? OR tracking_number LIKE ? OR customer_phone LIKE ? OR customer_email LIKE ?
            ORDER BY created_at DESC
        """, (f"%{search_q}%", f"%{search_q}%", f"%{search_q}%", f"%{search_q}%"))
    elif user_id:
        orders = query_db("SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    else:
        orders = query_db("SELECT * FROM orders ORDER BY created_at DESC LIMIT 10")

    return render_template('orders.html', orders=orders, search_query=search_q)

@app.route('/orders/<order_number>')
def order_detail(order_number):
    order = query_db("SELECT * FROM orders WHERE order_number = ?", (order_number,), one=True)
    if not order:
        flash('Order not found.', 'error')
        return redirect(url_for('orders_list'))

    items = query_db("SELECT * FROM order_items WHERE order_id = ?", (order['id'],))
    return render_template('order_detail.html', order=order, items=items)

@app.route('/wishlist')
def wishlist_page():
    user_id = session.get('user_id')
    if user_id:
        wishlist_products = query_db("""
            SELECT p.*, c.name as category_name 
            FROM wishlists w 
            JOIN products p ON w.product_id = p.id 
            LEFT JOIN categories c ON p.category_id = c.id 
            WHERE w.user_id = ?
            ORDER BY w.created_at DESC
        """, (user_id,))
    else:
        guest_ids = session.get('guest_wishlist', [])
        if guest_ids:
            placeholders = ','.join(['?'] * len(guest_ids))
            wishlist_products = query_db(f"""
                SELECT p.*, c.name as category_name 
                FROM products p 
                LEFT JOIN categories c ON p.category_id = c.id 
                WHERE p.id IN ({placeholders})
            """, guest_ids)
        else:
            wishlist_products = []

    return render_template('wishlist.html', wishlist_products=wishlist_products)

# ==============================================================================
# JSON AJAX API ENDPOINTS
# ==============================================================================

@app.route('/api/cart/add', methods=['POST'])
def api_cart_add():
    data = request.get_json() or {}
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))

    if not product_id:
        return jsonify({'success': False, 'message': 'Missing product ID'}), 400

    product = query_db("SELECT * FROM products WHERE id = ?", (product_id,), one=True)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404

    cart = get_cart()
    found = False
    for item in cart['items']:
        if item['product_id'] == product['id']:
            item['quantity'] += quantity
            found = True
            break

    if not found:
        cart['items'].append({
            'product_id': product['id'],
            'name': product['name'],
            'slug': product['slug'],
            'price': float(product['price']),
            'quantity': quantity,
            'image_url': product['image_url']
        })

    cart = recalculate_cart(cart)
    return jsonify({
        'success': True, 
        'message': f'"{product["name"]}" added to bag.',
        'cart': cart
    })

@app.route('/api/cart/update', methods=['POST'])
def api_cart_update():
    data = request.get_json() or {}
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))

    cart = get_cart()
    if quantity <= 0:
        cart['items'] = [item for item in cart['items'] if item['product_id'] != product_id]
    else:
        for item in cart['items']:
            if item['product_id'] == product_id:
                item['quantity'] = quantity
                break

    cart = recalculate_cart(cart)
    return jsonify({'success': True, 'cart': cart})

@app.route('/api/cart/clear', methods=['POST'])
def api_cart_clear():
    session['cart'] = {
        'items': [],
        'subtotal': 0.0,
        'discount_percent': 0.0,
        'coupon_code': None,
        'discount_amount': 0.0,
        'tax_amount': 0.0,
        'shipping_cost': 0.0,
        'total': 0.0
    }
    session.modified = True
    return jsonify({'success': True})

@app.route('/api/wishlist/toggle', methods=['POST'])
def api_wishlist_toggle():
    data = request.get_json() or {}
    product_id = data.get('product_id')
    user_id = session.get('user_id')

    if user_id:
        existing = query_db("SELECT id FROM wishlists WHERE user_id = ? AND product_id = ?", (user_id, product_id), one=True)
        if existing:
            execute_db("DELETE FROM wishlists WHERE id = ?", (existing['id'],))
            action = 'removed'
        else:
            execute_db("INSERT INTO wishlists (user_id, product_id) VALUES (?, ?)", (user_id, product_id))
            action = 'added'

        cnt = query_db("SELECT COUNT(*) as count FROM wishlists WHERE user_id = ?", (user_id,), one=True)['count']
    else:
        if 'guest_wishlist' not in session:
            session['guest_wishlist'] = []
        
        if product_id in session['guest_wishlist']:
            session['guest_wishlist'].remove(product_id)
            action = 'removed'
        else:
            session['guest_wishlist'].append(product_id)
            action = 'added'
        session.modified = True
        cnt = len(session['guest_wishlist'])

    return jsonify({'success': True, 'action': action, 'wishlist_count': cnt})

@app.route('/api/search')
def api_search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'products': []})

    products = query_db("""
        SELECT id, name, slug, price, image_url 
        FROM products 
        WHERE name LIKE ? OR description LIKE ? 
        LIMIT 6
    """, (f"%{q}%", f"%{q}%"))

    result = [{
        'id': p['id'],
        'name': p['name'],
        'slug': p['slug'],
        'price': float(p['price']),
        'image_url': p['image_url']
    } for p in products]

    return jsonify({'products': result})

# ==============================================================================
# AUTHENTICATION & CUSTOMER PROFILE
# ==============================================================================

@app.route('/auth')
def auth_page():
    if session.get('user_id'):
        return redirect(url_for('profile_page'))
    return render_template('auth.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    user = query_db("SELECT * FROM users WHERE email = ?", (email,), one=True)
    if not user or not check_password_hash(user['password_hash'], password):
        flash('Invalid email address or password combination.', 'error')
        return redirect(url_for('auth_page'))

    session['user_id'] = user['id']
    session['user_name'] = user['full_name']
    session['user_email'] = user['email']
    session['is_admin'] = bool(user['is_admin'])

    flash(f'Welcome back, {user["full_name"]}!', 'success')
    if user['is_admin']:
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('home'))

@app.route('/register', methods=['POST'])
def register():
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    phone = request.form.get('phone', '').strip()

    if not full_name or not email or not password:
        flash('Please fill in all mandatory fields.', 'error')
        return redirect(url_for('auth_page'))

    existing = query_db("SELECT id FROM users WHERE email = ?", (email,), one=True)
    if existing:
        flash('An account with this email address already exists.', 'error')
        return redirect(url_for('auth_page'))

    p_hash = generate_password_hash(password)
    user_id = execute_db("""
        INSERT INTO users (full_name, email, password_hash, is_admin, phone)
        VALUES (?, ?, ?, 0, ?)
    """, (full_name, email, p_hash, phone))

    session['user_id'] = user_id
    session['user_name'] = full_name
    session['user_email'] = email
    session['is_admin'] = False

    flash('Account created successfully! Welcome to Aethel & Co. VIP membership.', 'success')
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been securely signed out.', 'success')
    return redirect(url_for('home'))

@app.route('/profile')
def profile_page():
    if not session.get('user_id'):
        flash('Please sign in to access your profile.', 'error')
        return redirect(url_for('auth_page'))

    user = query_db("SELECT * FROM users WHERE id = ?", (session['user_id'],), one=True)
    return render_template('profile.html', user=user)

@app.route('/profile/update', methods=['POST'])
def profile_update():
    if not session.get('user_id'):
        return redirect(url_for('auth_page'))

    full_name = request.form.get('full_name', '').strip()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()
    city = request.form.get('city', '').strip()
    postal_code = request.form.get('postal_code', '').strip()

    execute_db("""
        UPDATE users 
        SET full_name = ?, phone = ?, address = ?, city = ?, postal_code = ? 
        WHERE id = ?
    """, (full_name, phone, address, city, postal_code, session['user_id']))

    session['user_name'] = full_name
    flash('Your profile details have been saved.', 'success')
    return redirect(url_for('profile_page'))

# ==============================================================================
# ADMIN MANAGEMENT PORTAL
# ==============================================================================

@app.route('/admin')
@admin_required
def admin_dashboard():
    total_rev_row = query_db("SELECT SUM(total_amount) as total FROM orders WHERE payment_status LIKE '%Paid%'", one=True)
    total_rev = total_rev_row['total'] if total_rev_row and total_rev_row['total'] else 0.0
    total_orders = query_db("SELECT COUNT(*) as count FROM orders", one=True)['count']
    total_products = query_db("SELECT COUNT(*) as count FROM products", one=True)['count']
    total_customers = query_db("SELECT COUNT(*) as count FROM users WHERE is_admin = 0", one=True)['count']

    recent_orders = query_db("SELECT * FROM orders ORDER BY created_at DESC LIMIT 6")
    low_stock_products = query_db("SELECT * FROM products WHERE stock <= 15 ORDER BY stock ASC LIMIT 5")

    return render_template('admin/dashboard.html',
                           total_revenue=total_rev,
                           total_orders=total_orders,
                           total_products=total_products,
                           total_customers=total_customers,
                           recent_orders=recent_orders,
                           low_stock_products=low_stock_products)

@app.route('/admin/products')
@admin_required
def admin_products():
    products = query_db("""
        SELECT p.*, c.name as category_name 
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.id 
        ORDER BY p.id DESC
    """)
    return render_template('admin/products.html', products=products)

@app.route('/admin/products/new', methods=['GET', 'POST'])
@admin_required
def admin_product_new():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        slug = name.lower().replace(' ', '-').replace('&', 'and').replace("'", '')
        category_id = request.form.get('category_id')
        badge = request.form.get('badge', '').strip()
        price = float(request.form.get('price', 0))
        original_price = float(request.form.get('original_price', 0)) if request.form.get('original_price') else None
        stock = int(request.form.get('stock', 10))
        image_url = request.form.get('image_url', '/static/images/products/luxury_watch.jpg').strip()
        short_desc = request.form.get('short_description', '').strip()
        description = request.form.get('description', '').strip()
        is_featured = 1 if request.form.get('is_featured') else 0
        is_trending = 1 if request.form.get('is_trending') else 0

        execute_db("""
            INSERT INTO products (
                name, slug, short_description, description, price, original_price,
                category_id, stock, image_url, is_featured, is_trending, badge
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, slug, short_desc, description, price, original_price, category_id, stock, image_url, is_featured, is_trending, badge))

        flash(f'Product "{name}" added to catalog.', 'success')
        return redirect(url_for('admin_products'))

    categories = query_db("SELECT * FROM categories ORDER BY name ASC")
    return render_template('admin/product_form.html', categories=categories, product=None)

@app.route('/admin/products/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_product_edit(product_id):
    product = query_db("SELECT * FROM products WHERE id = ?", (product_id,), one=True)
    if not product:
        flash('Product not found.', 'error')
        return redirect(url_for('admin_products'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category_id = request.form.get('category_id')
        badge = request.form.get('badge', '').strip()
        price = float(request.form.get('price', 0))
        original_price = float(request.form.get('original_price', 0)) if request.form.get('original_price') else None
        stock = int(request.form.get('stock', 10))
        image_url = request.form.get('image_url', '').strip()
        short_desc = request.form.get('short_description', '').strip()
        description = request.form.get('description', '').strip()
        is_featured = 1 if request.form.get('is_featured') else 0
        is_trending = 1 if request.form.get('is_trending') else 0

        execute_db("""
            UPDATE products 
            SET name = ?, short_description = ?, description = ?, price = ?,
                original_price = ?, category_id = ?, stock = ?, image_url = ?,
                is_featured = ?, is_trending = ?, badge = ?
            WHERE id = ?
        """, (name, short_desc, description, price, original_price, category_id, stock, image_url, is_featured, is_trending, badge, product_id))

        flash(f'Product "{name}" updated successfully.', 'success')
        return redirect(url_for('admin_products'))

    categories = query_db("SELECT * FROM categories ORDER BY name ASC")
    return render_template('admin/product_form.html', categories=categories, product=product)

@app.route('/admin/products/<int:product_id>/delete', methods=['POST'])
@admin_required
def admin_product_delete(product_id):
    execute_db("DELETE FROM products WHERE id = ?", (product_id,))
    flash('Product removed from catalog.', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
@admin_required
def admin_orders():
    orders = query_db("SELECT * FROM orders ORDER BY created_at DESC")
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def admin_order_status(order_id):
    status = request.form.get('status', 'Processing')
    tracking = request.form.get('tracking_number', '').strip()
    notes = request.form.get('notes', '').strip()

    if tracking and notes:
        execute_db("UPDATE orders SET order_status = ?, tracking_number = ?, notes = ? WHERE id = ?", (status, tracking, notes, order_id))
    elif tracking:
        execute_db("UPDATE orders SET order_status = ?, tracking_number = ? WHERE id = ?", (status, tracking, order_id))
    elif notes:
        execute_db("UPDATE orders SET order_status = ?, notes = ? WHERE id = ?", (status, notes, order_id))
    else:
        execute_db("UPDATE orders SET order_status = ? WHERE id = ?", (status, order_id))

    flash(f'Order #{order_id} fulfillment status updated to: {status}', 'success')
    return redirect(url_for('admin_orders'))

@app.route('/admin/coupons')
@admin_required
def admin_coupons():
    coupons = query_db("SELECT * FROM coupons ORDER BY created_at DESC")
    return render_template('admin/coupons.html', coupons=coupons)

@app.route('/admin/coupons/new', methods=['POST'])
@admin_required
def admin_coupon_new():
    code = request.form.get('code', '').strip().upper()
    discount_pct = float(request.form.get('discount_percent', 10))
    min_spend = float(request.form.get('min_spend', 0))

    try:
        execute_db("INSERT INTO coupons (code, discount_percent, min_spend, is_active) VALUES (?, ?, ?, 1)",
                   (code, discount_pct, min_spend))
        flash(f'Promo code {code} created with {discount_pct}% discount.', 'success')
    except Exception as e:
        flash(f'Error creating coupon: {e}', 'error')

    return redirect(url_for('admin_coupons'))

@app.route('/admin/coupons/<int:coupon_id>/delete', methods=['POST'])
@admin_required
def admin_coupon_delete(coupon_id):
    execute_db("DELETE FROM coupons WHERE id = ?", (coupon_id,))
    flash('Coupon deactivated and deleted.', 'success')
    return redirect(url_for('admin_coupons'))

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    if request.method == 'POST':
        keys = ['whatsapp_number', 'whatsapp_message', 'store_phone', 'store_email', 'store_name', 'store_address', 'banner_discount_code', 'currency_symbol']
        for k in keys:
            if k in request.form:
                set_setting(k, request.form.get(k, '').strip())
        flash('Store Contact & WhatsApp settings have been updated successfully!', 'success')
        return redirect(url_for('admin_settings'))

    current_settings = get_all_settings()
    return render_template('admin/settings.html', settings=current_settings)

# Custom Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() in ('true', '1', 'yes')
    print(f"Starting AURA Healthcare & Derma Labs server on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)

