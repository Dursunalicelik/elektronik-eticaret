import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
from database import init_db, get_db

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-development-key")
app.config["DATABASE"] = os.path.join(app.instance_path, "novastore.sqlite")
os.makedirs(app.instance_path, exist_ok=True)

with app.app_context():
    init_db(app.config["DATABASE"])

def current_user():
    if "user_id" not in session:
        return None
    db = get_db(app.config["DATABASE"])
    user = db.execute("SELECT id, name, email, is_admin FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    db.close()
    return user

@app.context_processor
def inject_globals():
    cart = session.get("cart", {})
    return {"current_user": current_user(), "cart_count": sum(cart.values())}

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user or not user["is_admin"]:
            flash("Bu sayfaya erişmek için yönetici girişi gerekli.", "error")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

@app.route("/")
def index():
    db = get_db(app.config["DATABASE"])
    products = db.execute("SELECT * FROM products ORDER BY id DESC LIMIT 8").fetchall()
    categories = db.execute("SELECT DISTINCT category FROM products ORDER BY category").fetchall()
    db.close()
    return render_template("index.html", products=products, categories=categories)

@app.route("/products")
def products():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    sort = request.args.get("sort", "newest")
    sql = "SELECT * FROM products WHERE 1=1"
    params = []
    if q:
        sql += " AND (name LIKE ? OR description LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]
    if category:
        sql += " AND category = ?"
        params.append(category)
    ordering = {"price_asc": "price ASC", "price_desc": "price DESC", "name": "name ASC"}.get(sort, "id DESC")
    sql += f" ORDER BY {ordering}"
    db = get_db(app.config["DATABASE"])
    items = db.execute(sql, params).fetchall()
    categories = db.execute("SELECT DISTINCT category FROM products ORDER BY category").fetchall()
    db.close()
    return render_template("products.html", products=items, categories=categories, q=q, selected_category=category, sort=sort)

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    db = get_db(app.config["DATABASE"])
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    db.close()
    if not product:
        abort(404)
    return render_template("product_detail.html", product=product)

@app.post("/cart/add/<int:product_id>")
def add_to_cart(product_id):
    db = get_db(app.config["DATABASE"])
    product = db.execute("SELECT id, stock FROM products WHERE id = ?", (product_id,)).fetchone()
    db.close()
    if not product:
        abort(404)
    cart = session.get("cart", {})
    key = str(product_id)
    if cart.get(key, 0) < product["stock"]:
        cart[key] = cart.get(key, 0) + 1
        session["cart"] = cart
        flash("Ürün sepetine eklendi.", "success")
    else:
        flash("Bu ürün için stok sınırına ulaştın.", "error")
    return redirect(request.referrer or url_for("products"))

@app.route("/cart")
def cart():
    cart_data = session.get("cart", {})
    ids = [int(i) for i in cart_data.keys()]
    items, total = [], 0
    if ids:
        db = get_db(app.config["DATABASE"])
        placeholders = ",".join("?" for _ in ids)
        rows = db.execute(f"SELECT * FROM products WHERE id IN ({placeholders})", ids).fetchall()
        db.close()
        for product in rows:
            quantity = min(cart_data.get(str(product["id"]), 1), product["stock"])
            subtotal = product["price"] * quantity
            total += subtotal
            items.append({"product": product, "quantity": quantity, "subtotal": subtotal})
    return render_template("cart.html", items=items, total=total)

@app.post("/cart/update/<int:product_id>")
def update_cart(product_id):
    quantity = request.form.get("quantity", type=int, default=1)
    db = get_db(app.config["DATABASE"])
    product = db.execute("SELECT stock FROM products WHERE id = ?", (product_id,)).fetchone()
    db.close()
    cart = session.get("cart", {})
    if not product or quantity <= 0:
        cart.pop(str(product_id), None)
    else:
        cart[str(product_id)] = min(quantity, product["stock"])
    session["cart"] = cart
    return redirect(url_for("cart"))

@app.post("/cart/remove/<int:product_id>")
def remove_from_cart(product_id):
    cart = session.get("cart", {})
    cart.pop(str(product_id), None)
    session["cart"] = cart
    flash("Ürün sepetten kaldırıldı.", "success")
    return redirect(url_for("cart"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 6:
            flash("Tüm alanları doldur. Şifre en az 6 karakter olmalı.", "error")
            return render_template("register.html")
        db = get_db(app.config["DATABASE"])
        try:
            cursor = db.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                                (name, email, generate_password_hash(password)))
            db.commit()
            session["user_id"] = cursor.lastrowid
            flash("Hesabın oluşturuldu.", "success")
            return redirect(url_for("index"))
        except Exception:
            flash("Bu e-posta adresi zaten kayıtlı olabilir.", "error")
        finally:
            db.close()
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        db = get_db(app.config["DATABASE"])
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        db.close()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            flash("Giriş başarılı.", "success")
            return redirect(url_for("admin") if user["is_admin"] else url_for("index"))
        flash("E-posta veya şifre hatalı.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Oturum kapatıldı.", "success")
    return redirect(url_for("index"))

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if not current_user():
        flash("Sipariş vermek için önce giriş yapmalısın.", "error")
        return redirect(url_for("login"))
    cart_data = session.get("cart", {})
    if not cart_data:
        flash("Sepetin boş.", "error")
        return redirect(url_for("products"))
    if request.method == "POST":
        address = request.form.get("address", "").strip()
        phone = request.form.get("phone", "").strip()
        if len(address) < 10 or not phone:
            flash("Lütfen geçerli adres ve telefon bilgisi gir.", "error")
            return render_template("checkout.html")
        db = get_db(app.config["DATABASE"])
        total = 0
        valid_items = []
        for pid, qty in cart_data.items():
            product = db.execute("SELECT * FROM products WHERE id = ?", (int(pid),)).fetchone()
            if product and qty > 0 and qty <= product["stock"]:
                total += product["price"] * qty
                valid_items.append((product, qty))
        if not valid_items:
            db.close()
            flash("Sepetindeki ürünler şu anda siparişe uygun değil.", "error")
            return redirect(url_for("cart"))
        cursor = db.execute("INSERT INTO orders (user_id, total, address, phone, status) VALUES (?, ?, ?, ?, ?)",
                            (session["user_id"], total, address, phone, "Hazırlanıyor"))
        order_id = cursor.lastrowid
        for product, qty in valid_items:
            db.execute("INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                       (order_id, product["id"], qty, product["price"]))
            db.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (qty, product["id"]))
        db.commit()
        db.close()
        session["cart"] = {}
        flash(f"Siparişin oluşturuldu. Sipariş numaran: #{order_id}. Ödeme alınmadı.", "success")
        return redirect(url_for("orders"))
    return render_template("checkout.html")

@app.route("/orders")
def orders():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    db = get_db(app.config["DATABASE"])
    rows = db.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (user["id"],)).fetchall()
    db.close()
    return render_template("orders.html", orders=rows)

@app.route("/admin")
@admin_required
def admin():
    db = get_db(app.config["DATABASE"])
    stats = {
        "products": db.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        "orders": db.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        "users": db.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "revenue": db.execute("SELECT COALESCE(SUM(total), 0) FROM orders").fetchone()[0]
    }
    latest = db.execute("SELECT orders.*, users.name AS customer FROM orders JOIN users ON users.id = orders.user_id ORDER BY orders.created_at DESC LIMIT 8").fetchall()
    products = db.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    db.close()
    return render_template("admin.html", stats=stats, latest=latest, products=products)

@app.route("/admin/product", methods=["POST"])
@admin_required
def admin_add_product():
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    description = request.form.get("description", "").strip()
    price = request.form.get("price", type=float)
    stock = request.form.get("stock", type=int)
    icon = request.form.get("icon", "📦")
    if name and category and description and price and price > 0 and stock is not None and stock >= 0:
        db = get_db(app.config["DATABASE"])
        db.execute("INSERT INTO products (name, category, description, price, stock, icon) VALUES (?, ?, ?, ?, ?, ?)",
                   (name, category, description, price, stock, icon))
        db.commit()
        db.close()
        flash("Ürün eklendi.", "success")
    else:
        flash("Ürün bilgilerini kontrol et.", "error")
    return redirect(url_for("admin"))

@app.post("/admin/product/delete/<int:product_id>")
@admin_required
def admin_delete_product(product_id):
    db = get_db(app.config["DATABASE"])
    db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    db.close()
    flash("Ürün silindi.", "success")
    return redirect(url_for("admin"))

@app.post("/admin/order/status/<int:order_id>")
@admin_required
def admin_order_status(order_id):
    status = request.form.get("status")
    allowed = ["Hazırlanıyor", "Kargoya verildi", "Teslim edildi", "İptal edildi"]
    if status in allowed:
        db = get_db(app.config["DATABASE"])
        db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        db.commit()
        db.close()
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(debug=True)
