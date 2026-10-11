import pandas as pd
import numpy as np

np.random.seed(11)

cust_df = pd.read_csv('data/dim_customer.csv')

months = pd.date_range('2022-07-01', '2024-06-01', freq='MS')  # 24 months

categories = ['Travel', 'Dining', 'Grocery', 'Fuel', 'Entertainment', 'Online Shopping', 'Utilities', 'Healthcare']

# seasonality index per category per month (1.0 = average)
seasonality = {
    'Travel':          {1:0.8,2:0.8,3:0.9,4:1.0,5:1.4,6:1.5,7:1.1,8:0.9,9:0.8,10:0.9,11:0.9,12:1.6},
    'Dining':          {1:0.9,2:0.9,3:1.0,4:1.0,5:1.0,6:1.0,7:1.0,8:1.0,9:1.0,10:1.1,11:1.15,12:1.3},
    'Grocery':         {1:1.0,2:1.0,3:1.0,4:1.0,5:1.0,6:1.0,7:1.0,8:1.0,9:1.0,10:1.05,11:1.1,12:1.15},
    'Fuel':             {1:1.0,2:1.0,3:1.0,4:1.0,5:1.0,6:1.0,7:1.0,8:1.0,9:1.0,10:1.0,11:1.0,12:1.05},
    'Entertainment':    {1:0.9,2:0.9,3:0.9,4:0.9,5:1.0,6:1.0,7:0.9,8:0.9,9:1.0,10:1.3,11:1.4,12:1.3},
    'Online Shopping':  {1:0.8,2:0.8,3:0.85,4:0.85,5:0.9,6:0.9,7:0.9,8:0.9,9:1.0,10:1.3,11:1.9,12:1.2},
    'Utilities':        {1:0.9,2:0.9,3:1.0,4:1.15,5:1.3,6:1.3,7:1.1,8:1.0,9:0.9,10:0.85,11:0.85,12:0.9},
    'Healthcare':       {1:0.9,2:0.9,3:0.95,4:1.0,5:1.0,6:1.0,7:1.1,8:1.15,9:1.15,10:1.0,11:0.95,12:0.95},
}

category_avg_spend = {
    'Travel': 8000, 'Dining': 3500, 'Grocery': 4500, 'Fuel': 3000,
    'Entertainment': 1800, 'Online Shopping': 5000, 'Utilities': 2500, 'Healthcare': 2000,
}

# Designate churn-risk customers (~12%) and high-growth customers (~10%)
n_churn = int(len(cust_df) * 0.12)
n_growth = int(len(cust_df) * 0.10)
churn_customers = set(np.random.choice(cust_df['customer_id'], size=n_churn, replace=False))
remaining = cust_df[~cust_df['customer_id'].isin(churn_customers)]
growth_customers = set(np.random.choice(remaining['customer_id'], size=n_growth, replace=False))

rows = []
for c in cust_df.itertuples():
    mult = category_spend_mult = {'Green': 0.7, 'Gold': 1.0, 'Platinum': 1.8, 'Centurion': 3.5}[c.card_type]
    is_churn = c.customer_id in churn_customers
    is_growth = c.customer_id in growth_customers
    cust_base_factor = np.random.uniform(0.6, 1.5)

    for m_idx, month in enumerate(months):
        month_num = month.month

        # churn decline starts month 15 (Sep 2023), growth acceleration starts month 12
        risk_factor = 1.0
        if is_churn and m_idx >= 15:
            decline_months = m_idx - 15
            risk_factor = max(0.05, 1 - 0.13 * decline_months)
        elif is_growth and m_idx >= 12:
            growth_months = m_idx - 12
            risk_factor = 1 + 0.05 * growth_months

        for cat in categories:
            seas = seasonality[cat][month_num]
            base = category_avg_spend[cat] * mult * cust_base_factor
            noise = np.random.normal(1.0, 0.25)
            spend = max(0, base * seas * risk_factor * noise)
            n_txn = max(0, int(np.random.poisson(spend / 1500) ))

            rows.append({
                'customer_id': c.customer_id,
                'date': month.strftime('%Y-%m-%d'),
                'year': month.year,
                'month': month_num,
                'category': cat,
                'spend': round(spend, 2),
                'num_transactions': n_txn,
            })

spend_df = pd.DataFrame(rows)
print("Total fact rows:", len(spend_df))
spend_df.to_csv('data/fact_monthly_spend.csv', index=False)

labels_df = pd.DataFrame({
    'customer_id': cust_df['customer_id'],
    'true_label': ['churn_risk' if c in churn_customers else ('high_growth' if c in growth_customers else 'stable')
                    for c in cust_df['customer_id']]
})
labels_df.to_csv('data/customer_true_labels.csv', index=False)
print(labels_df['true_label'].value_counts())
