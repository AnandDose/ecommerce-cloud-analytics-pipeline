import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()
random.seed(42)
np.random.seed(42)

# 1. GENERATE PRODUCTS
categories = ['Electronics', 'Apparel', 'Home & Kitchen', 'Beauty', 'Sports']
products_data = []
for prod_id in range(1001, 1051): # 50 products
    category = random.choice(categories)
    base_price = round(random.uniform(10.0, 500.0), 2)
    products_data.append({
        'product_id': prod_id,
        'product_name': f"{category} Item {fake.word().capitalize()}",
        'category': category,
        'base_price': base_price
    })
df_products = pd.DataFrame(products_data)
df_products.to_csv('products.csv', index=False)

# 2. GENERATE USERS
users_data = []
start_date = datetime(2025, 1, 1)
for user_id in range(1, 1001): # 1000 users
    signup_date = start_date + timedelta(days=random.randint(0, 365))
    users_data.append({
        'user_id': user_id,
        'name': fake.name(),
        'email': fake.email(),
        'country': random.choice(['US', 'CA', 'UK', 'DE', 'FR']),
        'signup_date': signup_date.strftime('%Y-%m-%d')
    })
df_users = pd.DataFrame(users_data)
df_users.to_csv('users.csv', index=False)

# 3. GENERATE TRANSACTIONS (With price variance for elasticity stats later)
tx_data = []
tx_id = 100001
for _, user in df_users.iterrows():
    # Give each user a random number of transactions (some 0, some many to simulate churn)
    num_tx = np.random.negative_binomial(n=2, p=0.3) 
    
    for _ in range(num_tx):
        prod = df_products.sample(1).iloc[0]
        # Introduce a price variation (-20% to +10%) to test elasticity later
        price_modifier = random.uniform(0.8, 1.1)
        actual_price = round(prod['base_price'] * price_modifier, 2)
        quantity = random.choices([1, 2, 3], weights=[80, 15, 5])[0]
        
        # Transaction date must be after signup date
        user_signup = datetime.strptime(user['signup_date'], '%Y-%m-%d')
        tx_date = user_signup + timedelta(days=random.randint(0, 90))
        
        tx_data.append({
            'transaction_id': tx_id,
            'user_id': user['user_id'],
            'product_id': prod['product_id'],
            'transaction_date': tx_date.strftime('%Y-%m-%d %H:%M:%S'),
            'quantity': quantity,
            'price_paid': actual_price
        })
        tx_id += 1

df_tx = pd.DataFrame(tx_data)
df_tx.to_csv('transactions.csv', index=False)

print(f"Data generation complete! Generated {len(df_products)} products, {len(df_users)} users, and {len(df_tx)} transactions.")