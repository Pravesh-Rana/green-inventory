# generate_data.py
import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()

# --- Configuration ---
NUM_CUSTOMERS = 200
NUM_PRODUCTS = 50
NUM_TRANSACTIONS = 5000

# --- Generate Products ---
product_names = ['Organic Milk 1L', 'Cheddar Cheese 250g', 'Sourdough Bread', 'Free-Range Eggs (12)', 'Granny Smith Apples', 'Chicken Breast 500g', 'Basmati Rice 1kg', 'Organic Tomatoes', 'Avocado', 'Dark Chocolate Bar']
products = {
    'ProductID': range(1, NUM_PRODUCTS + 1),
    'ProductName': [f"{random.choice(product_names)} v{i}" for i in range(1, NUM_PRODUCTS + 1)],
    'Category': [random.choice(['Dairy', 'Bakery', 'Produce', 'Meat', 'Pantry', 'Snacks']) for _ in range(NUM_PRODUCTS)],
    'CostPrice': np.round(np.random.uniform(1, 15, NUM_PRODUCTS), 2),
    'SellingPrice': np.round(np.random.uniform(2, 30, NUM_PRODUCTS), 2)
}
products_df = pd.DataFrame(products)

# --- Generate Customers ---
customers = {
    'CustomerID': range(1, NUM_CUSTOMERS + 1),
    'Name': [fake.name() for _ in range(NUM_CUSTOMERS)],
    'Age': np.random.randint(18, 70, NUM_CUSTOMERS),
    'Gender': [random.choice(['Male', 'Female', 'Other']) for _ in range(NUM_CUSTOMERS)],
    'JoinDate': [fake.date_this_decade() for _ in range(NUM_CUSTOMERS)]
}
customers_df = pd.DataFrame(customers)

# --- Generate Transactions ---
transactions = {
    'TransactionID': range(1, NUM_TRANSACTIONS + 1),
    'CustomerID': np.random.choice(customers['CustomerID'], NUM_TRANSACTIONS),
    'ProductID': np.random.choice(products['ProductID'], NUM_TRANSACTIONS),
    'Quantity': np.random.randint(1, 5, NUM_TRANSACTIONS),
    'TransactionDate': [datetime.now() - timedelta(days=random.randint(0, 365)) for _ in range(NUM_TRANSACTIONS)]
}
transactions_df = pd.DataFrame(transactions)

# --- Save to CSV ---
products_df.to_csv('products.csv', index=False)
customers_df.to_csv('customers.csv', index=False)
transactions_df.to_csv('transactions.csv', index=False)

print(f"Successfully generated: products.csv, customers.csv, transactions.csv")