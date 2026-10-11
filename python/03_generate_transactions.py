import pandas as pd
import numpy as np

np.random.seed(23)

cust_df = pd.read_csv('data/dim_customer.csv')
N_TXN = 60000

merchant_categories = ['Travel', 'Dining', 'Grocery', 'Fuel', 'Entertainment', 'Online Shopping', 'Utilities', 'Healthcare', 'Electronics', 'Jewellery']
mcc_avg_amount = {
    'Travel': 12000, 'Dining': 2200, 'Grocery': 2800, 'Fuel': 2500,
    'Entertainment': 1500, 'Online Shopping': 3500, 'Utilities': 2000,
    'Healthcare': 2500, 'Electronics': 15000, 'Jewellery': 35000,
}

sampled_customers = cust_df.sample(N_TXN, replace=True, random_state=1).reset_index(drop=True)

rows = []
FRAUD_RATE = 0.012  # ~1.2% of transactions flagged fraud (realistic imbalanced-class scenario)

for i in range(N_TXN):
    cust = sampled_customers.iloc[i]
    is_fraud = np.random.random() < FRAUD_RATE

    mcc = np.random.choice(merchant_categories)
    base_amt = mcc_avg_amount[mcc]
    card_mult = {'Green': 0.7, 'Gold': 1.0, 'Platinum': 1.8, 'Centurion': 3.5}[cust['card_type']]

    hour = int(np.clip(np.random.normal(14, 5), 0, 23))
    is_online = np.random.random() < 0.35
    is_international = np.random.random() < 0.03
    distance_from_home_km = max(0, np.random.exponential(15))

    if is_fraud:
        # fraud patterns: unusual amount, odd hours, more likely online/international, far from home
        amount = base_amt * np.random.uniform(3, 12)
        hour = np.random.choice([1, 2, 3, 4, 23], p=[0.25, 0.25, 0.2, 0.2, 0.1])
        is_online = np.random.random() < 0.75
        is_international = np.random.random() < 0.35
        distance_from_home_km = max(0, np.random.exponential(15) + np.random.uniform(200, 3000))
    else:
        amount = max(50, base_amt * card_mult * np.random.lognormal(0, 0.5))

    txn_date = pd.Timestamp('2023-07-01') + pd.Timedelta(days=int(np.random.uniform(0, 365)))

    rows.append({
        'transaction_id': f"TXN{str(i+1).zfill(7)}",
        'customer_id': cust['customer_id'],
        'card_type': cust['card_type'],
        'date': txn_date.strftime('%Y-%m-%d'),
        'hour_of_day': hour,
        'merchant_category': mcc,
        'amount': round(amount, 2),
        'is_online': int(is_online),
        'is_international': int(is_international),
        'distance_from_home_km': round(distance_from_home_km, 1),
        'is_fraud': int(is_fraud),
    })

txn_df = pd.DataFrame(rows)
txn_df.to_csv('data/fact_transactions.csv', index=False)
print("Total transactions:", len(txn_df))
print("Fraud count:", txn_df['is_fraud'].sum(), f"({txn_df['is_fraud'].mean()*100:.2f}%)")
