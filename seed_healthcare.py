import sqlite3
import os
from database import get_db_connection, init_db, generate_password_hash

def seed_pure_healthcare(force=False):
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    force_seed = force or os.environ.get('FORCE_SEED', '').lower() in ('true', '1', 'yes')

    # Check if database already has products or users
    if not force_seed:
        cursor.execute("SELECT COUNT(*) as count FROM products;")
        prod_count = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM users;")
        user_count = cursor.fetchone()['count']
        if prod_count > 0 and user_count > 0:
            print(f"Database already initialized ({prod_count} products, {user_count} users). Skipping seed to preserve data.")
            conn.close()
            return

    # Disable foreign keys temporarily for clean wipe & recreate
    cursor.execute("PRAGMA foreign_keys = OFF;")
    cursor.execute("DELETE FROM order_items;")
    cursor.execute("DELETE FROM orders;")
    cursor.execute("DELETE FROM reviews;")
    cursor.execute("DELETE FROM wishlists;")
    cursor.execute("DELETE FROM products;")
    cursor.execute("DELETE FROM categories;")
    cursor.execute("DELETE FROM coupons;")
    cursor.execute("DELETE FROM users;")
    cursor.execute("DELETE FROM sqlite_sequence;")
    cursor.execute("PRAGMA foreign_keys = ON;")

    print("Seeding pure Healthcare, Skincare, Serums, Shampoos & Wellness Store...")

    # 1. Users
    admin_hash = generate_password_hash("admin123")
    user_hash = generate_password_hash("user123")

    cursor.execute("""
    INSERT INTO users (full_name, email, password_hash, is_admin, phone, address, city, postal_code)
    VALUES (?, ?, ?, 1, ?, ?, ?, ?)
    """, ("Dr. Sarah Vance (Chief Medical Officer)", "admin@store.com", admin_hash, "0300 1234567", "Clinic #4, Healthcare City", "Islamabad", "44000"))

    cursor.execute("""
    INSERT INTO users (full_name, email, password_hash, is_admin, phone, address, city, postal_code)
    VALUES (?, ?, ?, 0, ?, ?, ?, ?)
    """, ("Muhammad Hamza", "user@store.com", user_hash, "0301 9876543", "House # 45, Street 10, Sector F-8", "Islamabad", "44000"))

    # 2. Healthcare Categories
    categories = [
        ("Active Facial Serums & Elixirs", "serums", "Clinical-strength L-Ascorbic Acid, Niacinamide, Hyaluronic Acid, and peptide cellular elixirs.", "/static/images/products/serum_dropper.jpg", "fa-flask-vial"),
        ("Botanical Shampoos & Haircare", "haircare", "Sulfate-free scalp cleansers, Biotin regrowth formulas, keratin masks, and follicle tonics.", "/static/images/products/botanical_shampoo.jpg", "fa-pump-soap"),
        ("Clinical Creams & Moisturizers", "creams", "Ceramide barrier repair treatments, copper peptide balms, and overnight collagen hydrators.", "/static/images/products/restorative_cream.jpg", "fa-spray-can-sparkles"),
        ("Gentle Cleansers & Face Washes", "cleansers", "pH-balanced botanical foam cleansers, AHA/BHA exfoliators, and deep pore clarifiers.", "/static/images/products/body_wash_botanical.jpg", "fa-soap"),
        ("Marine Collagen & Wellness", "supplements", "Hydrolyzed marine peptides, liposomal vitamins, and organic therapeutic supplements.", "/static/images/categories/healthcare.jpg", "fa-capsules"),
        ("Scalp Treatments & Hair Regrowth", "scalp-care", "Prebiotic follicle serums, rosemary essential tonics, and hair density elixirs.", "/static/images/products/scalp_tonic.jpg", "fa-droplet")
    ]

    cat_map = {}
    for cat in categories:
        cursor.execute("""
        INSERT INTO categories (name, slug, description, image_url, icon)
        VALUES (?, ?, ?, ?, ?)
        """, cat)
        cat_map[cat[1]] = cursor.lastrowid

    # 3. Healthcare Products
    products = [
        # SERUMS
        (
            "Botanical Cellular Renewal 20% Vitamin C & Niacinamide Serum",
            "botanical-cellular-renewal-vitamin-c-serum",
            "20% stabilized L-Ascorbic Acid, 5% Niacinamide, Ferulic Acid, and organic hyaluronic acid.",
            "Our gold-standard radiance serum. Clinically formulated with high-potency 20% L-Ascorbic Acid and Ferulic Acid to shield skin from oxidative stress, fade dark spots, and stimulate natural collagen synthesis. Packaged in pharmaceutical-grade light-blocking amber glass with precision calibrated dropper.",
            68.00, 88.00, cat_map["serums"], 40, 4.9, 94,
            "/static/images/products/serum_dropper.jpg", 1, 1, "Best Seller"
        ),
        (
            "Multi-Molecular 2% Hyaluronic Acid Deep Hydrating Plump Serum",
            "multi-molecular-hyaluronic-acid-plump-serum",
            "5 molecular weights of cross-linked Hyaluronic Acid, Pro-Vitamin B5, and Marine Algae.",
            "Provides instant multi-layer epidermal hydration for smooth, glass-like elasticity. Penetrates deeply into skin dermis to draw and lock in 1,000x its weight in moisture, visibly reducing dehydration lines and strengthening the skin barrier.",
            54.00, 72.00, cat_map["serums"], 35, 4.9, 68,
            "/static/images/products/hyaluronic_essence.jpg", 1, 1, "Top Rated"
        ),
        (
            "Retinol 1% + Squalane Age-Defying Cellular Renewal Serum",
            "retinol-1-squalane-age-defying-serum",
            "Micro-encapsulated pure Retinol, Plant Squalane, and Jojoba Oil extract.",
            "Accelerates cellular turnover to refine skin texture, fade fine lines, and boost firmness without redness or flakiness. Encapsulated in soothing pure sugarcane squalane for maximum tolerance.",
            72.00, 95.00, cat_map["serums"], 25, 4.8, 51,
            "/static/images/products/serum_dropper.jpg", 1, 0, "Derm Choice"
        ),
        (
            "Salicylic Acid 2% + Zinc BHA Pore-Minimizing Clarifying Serum",
            "salicylic-acid-2-zinc-bha-clarifying-serum",
            "2% Beta Hydroxy Acid (BHA), 1% Zinc PCA, and Organic Witch Hazel.",
            "Penetrates deep into sebaceous pores to dissolve excess sebum, unclog blackheads, and prevent breakout congestion. Balances oil production for a refined, shine-free matte complexion.",
            46.00, 60.00, cat_map["serums"], 30, 4.8, 42,
            "/static/images/products/serum_dropper.jpg", 0, 1, "Acne Defense"
        ),
        (
            "Copper Tripeptide-1 Youth Elasticity Booster Elixir",
            "copper-tripeptide-1-youth-elasticity-elixir",
            "Pure GHK-Cu Copper Peptides, Acetyl Hexapeptide-8, and Snow Mushroom Extract.",
            "A potent blue peptide elixir formulated to rebuild structural collagen, tighten sagging skin contours, and repair cellular micro-damage caused by UV exposure and blue light.",
            85.00, 110.00, cat_map["serums"], 18, 5.0, 39,
            "/static/images/products/serum_dropper.jpg", 1, 1, "Luxury Grade"
        ),

        # HAIRCARE & SHAMPOOS
        (
            "Caviar & Japanese Green Tea Volumizing Peptide Shampoo",
            "caviar-green-tea-volumizing-shampoo",
            "Sulfate-free formulation with Hydrolyzed Keratin, Biotin, and green tea polyphenols.",
            "Transform fine, flat, or thinning hair with restorative botanicals. Gently cleanses the scalp without stripping natural protective oils, infusing follicles with keratin proteins for long-lasting root lift, body, and luminous shine.",
            42.00, 55.00, cat_map["haircare"], 50, 4.9, 112,
            "/static/images/products/botanical_shampoo.jpg", 1, 1, "Award Winner"
        ),
        (
            "Rosemary & Biotin Anti-Hairfall Follicle Stimulating Shampoo",
            "rosemary-biotin-anti-hairfall-shampoo",
            "Cold-pressed Rosemary Extract, Biotin 5000mcg, Saw Palmetto, and Tea Tree.",
            "Specifically engineered to combat excessive hair shedding and thinning. Blocks DHT enzyme accumulation at root level while invigorating micro-circulation to promote healthy follicle longevity.",
            38.00, 49.00, cat_map["haircare"], 45, 4.8, 87,
            "/static/images/products/botanical_shampoo.jpg", 1, 1, "Trending"
        ),
        (
            "Moroccan Argan & Silk Protein Deep Restorative Hair Mask",
            "moroccan-argan-silk-protein-hair-mask",
            "Virgin Moroccan Argan Oil, Raw Shea Butter, Silk Amino Acids, and Keratin.",
            "An intensive weekly deep-conditioning salon treatment for dry, damaged, colored, or heat-styled hair. Fuses split ends, restores deep moisture, and eliminates frizz for silk-soft manageable hair.",
            48.00, 65.00, cat_map["haircare"], 28, 5.0, 56,
            "/static/images/products/hair_mask.jpg", 1, 0, "Salon Grade"
        ),
        (
            "Color Protect & Hydrate Botanical Conditioner",
            "color-protect-hydrate-botanical-conditioner",
            "Organic Aloe Vera, Coconut Milk, Marula Oil, and UV Color Shield complex.",
            "Lightweight detangling conditioner that locks in vibrant hair color pigments while delivering weightless hydration and high-definition natural shine.",
            36.00, 48.00, cat_map["haircare"], 35, 4.7, 34,
            "/static/images/products/botanical_shampoo.jpg", 0, 0, "Daily Essential"
        ),

        # CLINICAL CREAMS
        (
            "Midnight Peptide Barrier Repair & Collagen Recovery Cream",
            "midnight-peptide-barrier-repair-collagen-cream",
            "5 Bio-Ceramides, Copper Peptides, Centella Asiatica (Cica), and Plant Squalane.",
            "A rich, velvety night cream that accelerates nocturnal skin regeneration. Heals compromised skin barriers, seals in essential moisture, and leaves skin plump and glowing by morning.",
            78.00, 98.00, cat_map["creams"], 30, 4.9, 78,
            "/static/images/products/restorative_cream.jpg", 1, 1, "Doctor Recommended"
        ),
        (
            "Ceramide 5X Deep Hydration Barrier Water Gel",
            "ceramide-5x-deep-hydration-water-gel",
            "Essential Ceramides (1, 2, 3, 6-II), 3% Niacinamide, and Centella Water.",
            "Ultra-lightweight oil-free water gel cream formulated for combination, oily, and sensitive skin types. Delivers 48 hours of intense hydration without clogging pores or leaving greasy residue.",
            52.00, 68.00, cat_map["creams"], 40, 4.8, 63,
            "/static/images/products/restorative_cream.jpg", 0, 1, "Oil Free"
        ),
        (
            "Bakuchiol 2% Plant-Based Wrinkle Defense Day Cream",
            "bakuchiol-2-plant-based-wrinkle-defense-cream",
            "2% Pure Bakuchiol (Natural Retinol Alternative), Rosehip Seed Oil, and SPF 30.",
            "All the collagen-stimulating power of retinol without sensitivity to sunlight or skin peeling. Formulated with antioxidant botanical oils and broad-spectrum mineral UV filters for daytime protection.",
            65.00, 85.00, cat_map["creams"], 22, 4.9, 44,
            "/static/images/products/restorative_cream.jpg", 0, 0, "Clean Beauty"
        ),

        # CLEANSERS & FACE WASHES
        (
            "Nordic Sea Kelp & AHA Clarifying Exfoliating Face Cleanser",
            "nordic-sea-kelp-aha-clarifying-cleanser",
            "Lactic Acid (AHA), Wild Arctic Sea Kelp, Aloe Vera Leaf Juice, and Chamomile.",
            "A pH 5.5 daily gel cleanser that micro-exfoliates dull skin cells, removes waterproof makeup, and unblocks pores without tightness, dryness, or stinging.",
            38.00, 49.00, cat_map["cleansers"], 45, 4.8, 59,
            "/static/images/products/body_wash_botanical.jpg", 1, 1, "Staff Pick"
        ),
        (
            "Gentle Amino Acid Foaming Hydrating Cleanser",
            "gentle-amino-acid-foaming-cleanser",
            "11 Essential Amino Acids, Betaine, Colloidal Oatmeal, and Allantoin.",
            "Ultra-mild cloud-like foam cleanser designed specifically for barrier-compromised and hypersensitive skin. Removes impurities while soothing redness and irritation.",
            32.00, 42.00, cat_map["cleansers"], 55, 4.9, 73,
            "/static/images/products/body_wash_botanical.jpg", 0, 0, "Hypoallergenic"
        ),
        (
            "Activated Charcoal & Tea Tree Deep Pore Detox Wash",
            "activated-charcoal-tea-tree-pore-detox-wash",
            "Organic Activated Bamboo Charcoal, Australian Tea Tree Oil, and Eucalyptus.",
            "Draws out deep-seated urban environmental pollutants and stubborn micro-toxins from pores. Clears congestion and leaves skin deeply purified and refreshed.",
            36.00, 48.00, cat_map["cleansers"], 38, 4.7, 49,
            "/static/images/products/body_wash_botanical.jpg", 0, 1, "Detox Formula"
        ),

        # SUPPLEMENTS & WELLNESS
        (
            "Hydrolyzed Wild Marine Collagen Peptides (Type I & III)",
            "hydrolyzed-wild-marine-collagen-peptides",
            "100% Pure Norwegian Wild-Caught Marine Collagen, Hyaluronic Acid, and Vitamin C.",
            "High-bioavailability unflavored peptide powder that dissolves seamlessly into water, coffee, or smoothies. Clinically demonstrated to enhance skin firmness, hair thickness, and joint mobility in 30 days.",
            58.00, 75.00, cat_map["supplements"], 35, 4.9, 82,
            "/static/images/categories/healthcare.jpg", 1, 1, "Doctor Formulated"
        ),
        (
            "Liposomal High-Absorption Vitamin C + Glutathione 1000mg",
            "liposomal-vitamin-c-glutathione-1000mg",
            "Phospholipid Liposomal Vitamin C (1000mg) and Setria L-Glutathione (500mg).",
            "Up to 15x higher cellular bioavailability than regular vitamin C tablets. Strengthens systemic immune defense, neutralizes free radicals, and supports full-body skin brightening.",
            49.00, 65.00, cat_map["supplements"], 28, 4.9, 65,
            "/static/images/categories/healthcare.jpg", 0, 1, "Immunity Shield"
        ),
        (
            "Probiotic 50-Billion CFU Gut-Skin Axis Capsules",
            "probiotic-50-billion-cfu-gut-skin-capsules",
            "16 Clinically Studied Probiotic Strains + Organic Inulin Prebiotic Fiber.",
            "Optimizes digestive health and targets gut-induced skin inflammatory flare-ups. Delayed-release vegetarian acid-resistant capsules ensure live delivery to the intestinal tract.",
            45.00, 59.00, cat_map["supplements"], 40, 4.8, 38,
            "/static/images/categories/healthcare.jpg", 0, 0, "Gut Health"
        ),

        # SCALP & HAIR REGROWTH
        (
            "Prebiotic Rosemary & Peppermint Scalp Follicle Tonic",
            "prebiotic-rosemary-peppermint-scalp-tonic",
            "Cold-Extracted Rosemary Essential Oil, Peppermint, Caffeine 3%, and Redensyl.",
            "A fast-absorbing non-greasy leave-in scalp treatment that stimulates blood circulation around dormant hair roots, reactivating follicle growth and reducing thinning.",
            52.00, 68.00, cat_map["scalp-care"], 30, 4.9, 91,
            "/static/images/products/scalp_tonic.jpg", 1, 1, "Hair Regrowth"
        ),
        (
            "Cold-Pressed Jojoba & Castor Organic Hair Growth Elixir",
            "cold-pressed-jojoba-castor-hair-growth-elixir",
            "100% Organic Jamaican Black Castor Oil, Golden Jojoba, and Vitamin E.",
            "Nourishes dry scalp, prevents split-end breakage, and seals hair cuticles with essential fatty acids for accelerated length retention and density.",
            34.00, 45.00, cat_map["scalp-care"], 40, 4.8, 47,
            "/static/images/products/scalp_tonic.jpg", 0, 0, "100% Organic"
        )
    ]

    for p in products:
        cursor.execute("""
        INSERT INTO products (name, slug, short_description, description, price, original_price, category_id, stock, rating, review_count, image_url, is_featured, is_trending, badge)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, p)

    # 3.1 Product Gallery Additional Images
    cursor.execute("DELETE FROM product_images;")
    gallery_data = [
        (1, "/static/images/products/serum_dropper.jpg"),
        (1, "/static/images/products/hyaluronic_essence.jpg"),
        (2, "/static/images/products/hyaluronic_essence.jpg"),
        (2, "/static/images/products/serum_dropper.jpg"),
        (3, "/static/images/products/serum_dropper.jpg"),
        (6, "/static/images/products/botanical_shampoo.jpg"),
        (6, "/static/images/products/hair_mask.jpg"),
        (7, "/static/images/products/botanical_shampoo.jpg"),
        (7, "/static/images/products/scalp_tonic.jpg"),
        (8, "/static/images/products/hair_mask.jpg"),
        (8, "/static/images/products/botanical_shampoo.jpg"),
        (10, "/static/images/products/restorative_cream.jpg"),
        (10, "/static/images/products/serum_dropper.jpg"),
        (11, "/static/images/products/restorative_cream.jpg"),
        (13, "/static/images/products/body_wash_botanical.jpg"),
        (16, "/static/images/categories/healthcare.jpg"),
        (19, "/static/images/products/scalp_tonic.jpg"),
        (19, "/static/images/products/botanical_shampoo.jpg"),
    ]
    for pid, img in gallery_data:
        cursor.execute("INSERT INTO product_images (product_id, image_url) VALUES (?, ?)", (pid, img))

    # 4. Coupons
    coupons = [
        ("HEALTH20", 20.0, 30.0, 1),
        ("CARE10", 10.0, 0.0, 1),
        ("DERMA50", 50.0, 80.0, 1),
        ("FREESHIP", 5.0, 0.0, 1),
    ]

    for c in coupons:
        cursor.execute("""
        INSERT INTO coupons (code, discount_percent, min_spend, is_active)
        VALUES (?, ?, ?, ?)
        """, c)

    # 5. Reviews
    sample_reviews = [
        (1, 2, "Dr. Emily Watson, MD", 5, "Remarkable clinical efficacy!", "The 20% L-Ascorbic formulation is on par with $180 medical-grade dermatological serums. Noticeable glow and fade of sun spots in 10 days."),
        (1, None, "Zainab Fatima", 5, "My holy grail serum", "Lightweight, absorbs instantly, zero stickiness. Works wonderfully under makeup and sunscreen."),
        (2, None, "Amina Tariq", 5, "Deeply plumping and hydrating", "Restored my skin barrier after over-exfoliating. No dry patches anymore."),
        (6, 2, "Hamza Khan", 5, "Best volumizing shampoo hands down", "Gives so much bounce and body without drying out the scalp. Smells like a luxury spa."),
        (7, None, "Bilal Siddiqui", 5, "Hair shedding reduced by 80%", "After 3 weeks of combining the rosemary shampoo and scalp tonic, my hairline is visibly fuller."),
        (10, None, "Sana Merchant", 5, "Woke up with baby soft skin", "The midnight peptide cream is pure magic for tired, stressed skin.")
    ]

    for r in sample_reviews:
        cursor.execute("""
        INSERT INTO reviews (product_id, user_id, user_name, rating, title, comment)
        VALUES (?, ?, ?, ?, ?, ?)
        """, r)

    # 6. Sample Initial Orders (COD / Direct Card)
    cursor.execute("""
    INSERT INTO orders (order_number, user_id, customer_name, customer_email, customer_phone, shipping_address, city, postal_code, country, shipping_method, payment_method, payment_status, payment_account, transaction_reference, subtotal, discount_amount, shipping_cost, tax_amount, total_amount, coupon_code, order_status, tracking_number)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "ORD-2026-9042", 2, "Muhammad Hamza", "user@store.com", "0301 9876543",
        "House # 45, Street 10, Sector F-8", "Islamabad", "44000", "Pakistan",
        "Complimentary Express Courier (TCS)", "Cash on Delivery (COD)", "Pending (Cash on Delivery)",
        "0301 9876543", "COD-98210344", 110.00, 22.00, 0.00, 7.04, 95.04, "HEALTH20", "Processing", "TCS-990011283"
    ))
    order_1_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO order_items (order_id, product_id, product_name, price, quantity, image_url)
    VALUES (?, 1, 'Botanical Cellular Renewal 20% Vitamin C & Niacinamide Serum', 68.00, 1, '/static/images/products/serum_dropper.jpg')
    """, (order_1_id,))
    cursor.execute("""
    INSERT INTO order_items (order_id, product_id, product_name, price, quantity, image_url)
    VALUES (?, 6, 'Caviar & Japanese Green Tea Volumizing Peptide Shampoo', 42.00, 1, '/static/images/products/botanical_shampoo.jpg')
    """, (order_1_id,))

    cursor.execute("""
    INSERT INTO orders (order_number, user_id, customer_name, customer_email, customer_phone, shipping_address, city, postal_code, country, shipping_method, payment_method, payment_status, payment_account, transaction_reference, subtotal, discount_amount, shipping_cost, tax_amount, total_amount, coupon_code, order_status, tracking_number)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "ORD-2026-9155", None, "Ayesha Malik", "ayesha@example.com", "0300 4455667",
        "DHA Phase 6, Sector B", "Lahore", "54000", "Pakistan",
        "Complimentary Express Courier (Leopards)", "Cash on Delivery (COD)", "Pending (Cash on Delivery)",
        "0300 4455667", "COD-DOORSTEP", 126.00, 12.60, 0.00, 9.07, 122.47, "CARE10", "Shipped", "LEO-77112093"
    ))
    order_2_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO order_items (order_id, product_id, product_name, price, quantity, image_url)
    VALUES (?, 10, 'Midnight Peptide Barrier Repair & Collagen Recovery Cream', 78.00, 1, '/static/images/products/restorative_cream.jpg')
    """, (order_2_id,))
    cursor.execute("""
    INSERT INTO order_items (order_id, product_id, product_name, price, quantity, image_url)
    VALUES (?, 8, 'Moroccan Argan & Silk Protein Deep Restorative Hair Mask', 48.00, 1, '/static/images/products/hair_mask.jpg')
    """, (order_2_id,))

    conn.commit()
    conn.close()
    print("Pure Healthcare Store Database initialized and seeded with 20 clinical products!")

if __name__ == '__main__':
    seed_pure_healthcare()
