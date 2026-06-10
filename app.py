from flask import Flask, jsonify, render_template, request
import sqlite3
import datetime

app = Flask(__name__)
DB_NAME = "shopping.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        reward_points INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        total_price REAL NOT NULL,
        discount REAL DEFAULT 0,
        final_price REAL NOT NULL,
        date TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS rewards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        points_earned INTEGER NOT NULL,
        reason TEXT NOT NULL,
        date TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    # Seed sample products
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        products = [
            ("Laptop", "Electronics", 55000.0, 10),
            ("Phone", "Electronics", 15000.0, 25),
            ("Headphones", "Electronics", 2000.0, 50),
            ("T-Shirt", "Clothing", 499.0, 100),
            ("Jeans", "Clothing", 1299.0, 60),
            ("Novel - Fiction", "Books", 350.0, 200),
            ("Python Programming", "Books", 650.0, 80),
            ("Backpack", "Accessories", 999.0, 40),
        ]
        c.executemany("INSERT INTO products (name, category, price, stock) VALUES (?,?,?,?)", products)

    conn.commit()
    conn.close()

# ---- Users ----
@app.route("/api/users", methods=["GET"])
def get_users():
    conn = get_db()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return jsonify([dict(u) for u in users])

@app.route("/api/users", methods=["POST"])
def add_user():
    data = request.json
    conn = get_db()
    try:
        conn.execute("INSERT INTO users (name, email) VALUES (?,?)", (data["name"], data["email"]))
        conn.commit()
        user = conn.execute("SELECT * FROM users WHERE email=?", (data["email"],)).fetchone()
        conn.close()
        return jsonify(dict(user)), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Email already exists"}), 400

# ---- Products ----
@app.route("/api/products", methods=["GET"])
def get_products():
    conn = get_db()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return jsonify([dict(p) for p in products])

# ---- Purchase ----
@app.route("/api/purchase", methods=["POST"])
def purchase():
    data = request.json
    user_id = data["user_id"]
    product_id = data["product_id"]
    quantity = int(data["quantity"])

    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

    if not product or not user:
        conn.close()
        return jsonify({"error": "User or product not found"}), 404

    if product["stock"] < quantity:
        conn.close()
        return jsonify({"error": "Not enough stock"}), 400

    total_price = product["price"] * quantity

    # Discount logic: 10% if points >= 100, 5% if points >= 50
    discount = 0
    if user["reward_points"] >= 100:
        discount = 0.10
    elif user["reward_points"] >= 50:
        discount = 0.05

    final_price = round(total_price * (1 - discount), 2)
    points_earned = int(final_price // 100)  # 1 point per 100 spent
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn.execute(
        "INSERT INTO transactions (user_id, product_id, quantity, total_price, discount, final_price, date) VALUES (?,?,?,?,?,?,?)",
        (user_id, product_id, quantity, total_price, discount * 100, final_price, date)
    )
    conn.execute("UPDATE products SET stock = stock - ? WHERE id=?", (quantity, product_id))
    conn.execute("UPDATE users SET reward_points = reward_points + ? WHERE id=?", (points_earned, user_id))
    conn.execute(
        "INSERT INTO rewards (user_id, points_earned, reason, date) VALUES (?,?,?,?)",
        (user_id, points_earned, f"Purchase of {product['name']} x{quantity}", date)
    )
    conn.commit()

    updated_user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()

    return jsonify({
        "message": "Purchase successful",
        "product": product["name"],
        "quantity": quantity,
        "total_price": total_price,
        "discount_applied": f"{int(discount*100)}%",
        "final_price": final_price,
        "points_earned": points_earned,
        "total_reward_points": updated_user["reward_points"]
    }), 201

# ---- Summary ----
@app.route("/api/summary/<int:user_id>", methods=["GET"])
def get_summary(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404

    transactions = conn.execute("""
        SELECT t.*, p.name as product_name
        FROM transactions t
        JOIN products p ON t.product_id = p.id
        WHERE t.user_id = ?
        ORDER BY t.date DESC
    """, (user_id,)).fetchall()

    monthly = conn.execute("""
        SELECT strftime('%Y-%m', date) as month, SUM(final_price) as total_spent
        FROM transactions WHERE user_id=?
        GROUP BY month ORDER BY month DESC
    """, (user_id,)).fetchall()

    conn.close()
    return jsonify({
        "user": dict(user),
        "transactions": [dict(t) for t in transactions],
        "monthly_summary": [dict(m) for m in monthly]
    })

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
