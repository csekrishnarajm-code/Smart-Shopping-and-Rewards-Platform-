# Smart Shopping and Rewards Platform

A full-stack web application that allows customers to register, browse products, make purchases, apply personalized discounts based on reward points, and view monthly expense summaries.

## Features
- Customer registration and profile management
- Product catalog with 500+ records across 4 categories
- Purchase system with automatic discount calculation based on reward points
- Reward points earned on every purchase (1 point per ₹100 spent)
- Discount tiers: 10% off (100+ points), 5% off (50+ points)
- Monthly expense summary per customer
- Full CRUD operations with referential integrity across 4 database tables

## Tech Stack
- **Backend:** Python, Flask
- **Database:** SQLite (MySQL-compatible SQL schema)
- **Frontend:** HTML, CSS, JavaScript (Vanilla)
- **API:** REST

## Database Schema (4 Tables)
```
users          → id, name, email, reward_points
products       → id, name, category, price, stock
transactions   → id, user_id, product_id, quantity, total_price, discount, final_price, date
rewards        → id, user_id, points_earned, reason, date
```
Foreign key relationships: transactions and rewards reference users and products.

## Project Structure
```
smart-shopping-rewards/
├── app.py              # Flask app, REST API, database logic
├── shopping.db         # SQLite database (auto-created)
├── requirements.txt    # Dependencies
└── templates/
    └── index.html      # Frontend UI
```

## How to Run

### 1. Clone the repository
```bash
git clone https://github.com/Krishnarajm008/smart-shopping-rewards.git
cd smart-shopping-rewards
```

### 2. Install dependencies
```bash
pip install flask
```

### 3. Run the app
```bash
python app.py
```

### 4. Open in browser
```
http://127.0.0.1:5000
```

## What I Learned
- Designing a relational database schema with foreign key constraints
- Building REST APIs with Flask
- Implementing business logic (discount tiers, reward points)
- Connecting backend data to a dynamic frontend with vanilla JavaScript
