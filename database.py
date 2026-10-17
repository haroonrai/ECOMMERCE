import sqlite3
import os
import hashlib
import secrets
from datetime import datetime

DB_PATH_ENV = os.environ.get('DATABASE_PATH')
if DB_PATH_ENV:
    DB_FILE = os.path.abspath(DB_PATH_ENV)
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
else:
    DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ecommerce.db')

def generate_password_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"pbkdf2:sha256:100000${salt}${key.hex()}"

def check_password_hash(hash_val: str, password: str) -> bool:
    try:
        parts = hash_val.split('$')
        if len(parts) != 3:
            return False
        method, salt, key_hex = parts
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return secrets.compare_digest(key.hex(), key_hex)
    except Exception:
        return False

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0,
        phone TEXT,
        address TEXT,
        city TEXT,
        postal_code TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    # Categories Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        description TEXT,
        image_url TEXT,
        icon TEXT
    );
    ''')

    # Products Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        short_description TEXT,
        description TEXT,
        price REAL NOT NULL,
        original_price REAL,
        category_id INTEGER,
        stock INTEGER DEFAULT 10,
        rating REAL DEFAULT 5.0,
        review_count INTEGER DEFAULT 0,
        image_url TEXT NOT NULL,
        is_featured INTEGER DEFAULT 0,
        is_trending INTEGER DEFAULT 0,
        badge TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
    );
    ''')

    # Product Additional Gallery Images
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS product_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        image_url TEXT NOT NULL,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
    );
    ''')

    # Product Reviews
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        user_id INTEGER,
        user_name TEXT NOT NULL,
        rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
        title TEXT,
        comment TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    ''')

    # Coupons / Promo Codes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS coupons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        discount_percent REAL NOT NULL,
        min_spend REAL DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    # Orders Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT UNIQUE NOT NULL,
        user_id INTEGER,
        customer_name TEXT NOT NULL,
        customer_email TEXT NOT NULL,
        customer_phone TEXT,
        shipping_address TEXT NOT NULL,
        city TEXT NOT NULL,
        postal_code TEXT,
        country TEXT DEFAULT 'Pakistan',
        shipping_method TEXT DEFAULT 'Standard Shipping',
        payment_method TEXT NOT NULL,
        payment_status TEXT DEFAULT 'Paid',
        payment_account TEXT,
        transaction_reference TEXT,
        subtotal REAL NOT NULL,
        discount_amount REAL DEFAULT 0,
        shipping_cost REAL DEFAULT 0,
        tax_amount REAL DEFAULT 0,
        total_amount REAL NOT NULL,
        coupon_code TEXT,
        order_status TEXT DEFAULT 'Processing',
        tracking_number TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    ''')

    # Migration for existing DB
    try:
        cursor.execute("ALTER TABLE orders ADD COLUMN payment_account TEXT;")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE orders ADD COLUMN transaction_reference TEXT;")
    except Exception:
        pass

    # Order Items Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER,
        product_name TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        image_url TEXT,
        FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
    );
    ''')

    # Wishlist Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS wishlists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, product_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
    );
    ''')

    # Settings Table for Store & Contact Configurations
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    ''')

    # Seed default store settings if missing
    default_settings = {
        'whatsapp_number': os.environ.get('WHATSAPP_NUMBER', '+92 300 1234567'),
        'whatsapp_message': 'Hi AURA Healthcare, I would like a consultation regarding skincare and hair formulations.',
        'store_phone': '+92 300 1234567',
        'store_email': 'support@auracare.com',
        'store_name': 'AURA Healthcare & Derma Labs',
        'store_address': 'Clinical Derma Complex, Gulberg III, Lahore, Pakistan',
        'banner_discount_code': 'HEALTH20',
        'currency_symbol': '$'
    }

    for k, v in default_settings.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    conn.commit()
    conn.close()

def get_all_settings():
    try:
        rows = query_db("SELECT key, value FROM settings")
        return {r['key']: r['value'] for r in rows}
    except Exception:
        return {}

def get_setting(key, default=None):
    try:
        row = query_db("SELECT value FROM settings WHERE key = ?", (key,), one=True)
        return row['value'] if row else default
    except Exception:
        return default

def set_setting(key, value):
    try:
        execute_db("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, str(value)))
        return True
    except Exception:
        return False

def query_db(query, args=(), one=False):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=(), commit=True):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, args)
    last_id = cur.lastrowid
    if commit:
        conn.commit()
    conn.close()
    return last_id

