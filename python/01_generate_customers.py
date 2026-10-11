import pandas as pd
import numpy as np

np.random.seed(42)

N_CUSTOMERS = 1500

card_types = ['Green', 'Gold', 'Platinum', 'Centurion']
card_weights = [0.45, 0.30, 0.20, 0.05]  # most customers on entry-level cards
card_credit_limit_base = {'Green': 80000, 'Gold': 200000, 'Platinum': 500000, 'Centurion': 1500000}
card_spend_multiplier = {'Green': 0.7, 'Gold': 1.0, 'Platinum': 1.8, 'Centurion': 3.5}

cities = ['Mumbai', 'Delhi', 'Bengaluru', 'Chennai', 'Hyderabad', 'Pune', 'Kolkata', 'Ahmedabad', 'Jaipur', 'Chandigarh']
city_weights = [0.18, 0.16, 0.15, 0.09, 0.09, 0.08, 0.07, 0.06, 0.06, 0.06]

income_brackets = ['5-10L', '10-20L', '20-40L', '40L+']
income_weights = [0.35, 0.35, 0.20, 0.10]

customers = []
for i in range(1, N_CUSTOMERS + 1):
    card = np.random.choice(card_types, p=card_weights)
    city = np.random.choice(cities, p=city_weights)
    income = np.random.choice(income_brackets, p=income_weights)
    age = int(np.clip(np.random.normal(38, 10), 22, 70))
    tenure_months = int(np.random.uniform(3, 96))  # 3 months to 8 years
    credit_limit = int(card_credit_limit_base[card] * np.random.uniform(0.7, 1.4))

    customers.append({
        'customer_id': f"CUST{str(i).zfill(5)}",
        'card_type': card,
        'city': city,
        'income_bracket': income,
        'age': age,
        'tenure_months': tenure_months,
        'credit_limit': credit_limit,
        'signup_date': (pd.Timestamp('2024-06-01') - pd.DateOffset(months=tenure_months)).strftime('%Y-%m-%d'),
    })

cust_df = pd.DataFrame(customers)
cust_df.to_csv('data/dim_customer.csv', index=False)
print("Customers generated:", len(cust_df))
print(cust_df['card_type'].value_counts())
