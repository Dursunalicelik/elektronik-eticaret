import sqlite3
from flask import current_app, g

def get_db(path=None):
    if path is None:
        path = current_app.config["DATABASE"]
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    return db

def init_db(path):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        is_admin INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL DEFAULT 0,
        icon TEXT NOT NULL DEFAULT '📦',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total REAL NOT NULL,
        address TEXT NOT NULL,
        phone TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Hazırlanıyor',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        FOREIGN KEY(order_id) REFERENCES orders(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    );
    """)
    count = db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count == 0:
        seed = [
            ("NovaBook Air 14", "Bilgisayar", "Günlük kullanım ve üretkenlik için hafif, hızlı dizüstü bilgisayar.", 24999, 12, "💻"),
            ("NovaPhone X", "Telefon", "Canlı ekranı ve güçlü kamerasıyla günlük hayatın için.", 18999, 20, "📱"),
            ("Sonic Pro Kulaklık", "Ses", "Konforlu tasarım, net ses ve uzun pil ömrü.", 2499, 35, "🎧"),
            ("NovaTab 11", "Tablet", "Ders, çizim ve eğlence için çok yönlü tablet.", 9999, 15, "📟"),
            ("Pulse Akıllı Saat", "Akıllı Saat", "Aktivite takibi ve bildirimler tek ekranda.", 3299, 28, "⌚"),
            ("Mech Mini Klavye", "Aksesuar", "Kompakt mekanik klavye ile çalışma alanını düzenle.", 1799, 40, "⌨️"),
            ("AirBeat Hoparlör", "Ses", "Kompakt gövdede güçlü ve dengeli ses.", 2199, 18, "🔊"),
            ("NovaCam 4K", "Kamera", "Net görüntülü toplantılar ve içerik üretimi için.", 4599, 9, "📷"),
        ]
        db.executemany("INSERT INTO products (name, category, description, price, stock, icon) VALUES (?, ?, ?, ?, ?, ?)", seed)
    # Demo admin: change the password immediately after first login.
    admin = db.execute("SELECT id FROM users WHERE email = ?", ("admin@novastore.local",)).fetchone()
    if not admin:
        from werkzeug.security import generate_password_hash
        db.execute("INSERT INTO users (name, email, password_hash, is_admin) VALUES (?, ?, ?, 1)",
                   ("NovaStore Admin", "admin@novastore.local", generate_password_hash("NovaAdmin123!")))
    db.commit()
    db.close()
